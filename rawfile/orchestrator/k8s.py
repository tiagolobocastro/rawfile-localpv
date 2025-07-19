from typing import Any, TypedDict
import uuid
from subprocess import CalledProcessError
from time import sleep

import re
from datetime import datetime
from consts import CONFIG, VOLUME_IS_ATTACHED
from kubernetes import client as k8s_client, config as k8s_config
from utils.logs import LoggingFormats, logger, format as log_format, level as log_level

k8s_config.load_config()


class TaskPodInfo(TypedDict):
    name: str
    namespace: str
    datadir: str
    node_selector: dict[str, str]
    image_repository: str
    image_tag: str
    log_format: LoggingFormats
    log_level: str
    reserved_capacity: int | str
    capacity_override: int
    command: str


def generate_task_pod_manifest(info: TaskPodInfo) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"name": info["name"], "namespace": info["namespace"]},
        "spec": {
            "restartPolicy": "Never",
            "terminationGracePeriodSeconds": 0,
            "tolerations": [{"operator": "Exists"}],
            "volumes": [
                {
                    "name": "data-dir",
                    "hostPath": {"path": info["datadir"], "type": "DirectoryOrCreate"},
                },
                {"name": "device", "hostPath": {"path": "/dev", "type": "Directory"}},
            ],
            "nodeSelector": info["node_selector"],
            "containers": [
                {
                    "name": "task",
                    "image": f"{info['image_repository']}:{info['image_tag']}",
                    "imagePullPolicy": "IfNotPresent",
                    "volumeMounts": [
                        {"name": "data-dir", "mountPath": "/data"},
                        {"name": "device", "mountPath": "/dev"},
                    ],
                    "resources": {
                        "requests": {"cpu": "0m", "memory": "0Mi"},
                        "limits": {"cpu": "100m", "memory": "100Mi"},
                    },
                    "env": [
                        {
                            "name": "LOG_FORMAT",
                            "value": str(info["log_format"].value),
                        },
                        {"name": "LOG_LEVEL", "value": info["log_level"]},
                        {
                            "name": "reserved_capacity",
                            "value": str(info["reserved_capacity"]),
                        },
                        {
                            "name": "CAPACITY_OVERRIDE",
                            "value": str(info["capacity_override"]),
                        },
                    ],
                    "command": ["/bin/sh", "-c"],
                    "args": [info["command"]],
                }
            ],
        },
    }


def volume_to_node(volume_id):
    api = k8s_client.CoreV1Api()
    pv: k8s_client.V1PersistentVolume = api.read_persistent_volume(name=volume_id)
    curr_node_affinity: k8s_client.V1VolumeNodeAffinity = pv.spec.node_affinity
    node_name = (
        curr_node_affinity.required.node_selector_terms[0]
        .match_expressions[0]
        .values[0]
    )
    expected_affinity = k8s_client.V1VolumeNodeAffinity(
        required=k8s_client.V1NodeSelector(
            [
                k8s_client.V1NodeSelectorTerm(
                    match_expressions=[
                        k8s_client.V1NodeSelectorRequirement(
                            key="hostname", operator="In", values=[node_name]
                        )
                    ]
                )
            ]
        )
    )
    assert curr_node_affinity == expected_affinity
    return node_name


def wait_for(pred, desc=""):
    start = datetime.now()
    while not pred():
        sleep(0.5)
    end = datetime.now()
    logger.info(
        f"Finished waiting for {desc}", start=start, end=end, latency=end - start
    )


def run_on_node(fn, node):
    api = k8s_client.CoreV1Api()
    name = f"task-{uuid.uuid4()}"
    registry = CONFIG["image_registry"]
    repository = CONFIG["image_repository"]
    ctx: TaskPodInfo = {
        "name": name,
        "namespace": CONFIG["namespace"],
        "node_selector": {"kubernetes.io/hostname": node},
        "command": fn,
        "image_repository": (
            f"{registry}/{repository}" if registry is not None else repository
        ),
        "image_tag": CONFIG["image_tag"],
        "datadir": CONFIG["node_datadir"],
        "log_format": log_format,
        "log_level": log_level,
        "reserved_capacity": CONFIG["reserved_capacity"],
        "capacity_override": CONFIG.get("capacity_override", 0),
    }
    manifest = generate_task_pod_manifest(ctx)
    logger.debug("Creating task pod", manifest=manifest)
    api.create_namespaced_pod(
        namespace=CONFIG["namespace"],
        body=manifest,
    )

    def is_finished():
        task_pod = api.read_namespaced_pod(name=name, namespace=CONFIG["namespace"])
        status = task_pod.status
        if status.phase in ("Succeeded", "Failed"):
            return True
        return False

    wait_for(is_finished, "task to finish")
    task_pod = api.read_namespaced_pod(name=name, namespace=CONFIG["namespace"])
    status = task_pod.status
    logs = api.read_namespaced_pod_log(
        name=name, namespace=CONFIG["namespace"], container="task"
    )
    api.delete_namespaced_pod(name=name, namespace=CONFIG["namespace"])

    if status.phase != "Succeeded":
        exit_code = status.container_statuses[0].state.terminated.exit_code
        logger.error(
            "Task failed", exit_code=exit_code, output=logs, pod_name=name, node=node
        )
        raise CalledProcessError(returncode=exit_code, cmd=f"Task: {name}", output=logs)

    match = re.search(f"{VOLUME_IS_ATTACHED}=(True|False)", logs)
    is_attached = match.group(1) == "True" if match else None
    return is_attached

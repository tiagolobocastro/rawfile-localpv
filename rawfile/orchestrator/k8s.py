import json
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from time import sleep

import re
import yaml
from datetime import datetime
from consts import CONFIG, VOLUME_IS_ATTACHED
from kubernetes import client as k8s_client, config as k8s_config
from utils.logs import logger, format as log_format, level as log_level

k8s_config.load_config()


def volume_to_node(volume_id):
    api = k8s_client.CoreV1Api()
    pv = api.read_persistent_volume(name=volume_id)
    node_name = (
        pv.spec.node_affinity.required.node_selector_terms[0]
        .match_expressions[0]
        .values[0]
    )
    assert all(
        (
            len(pv.spec.node_affinity.required.node_selector_terms) == 1,
            len(pv.spec.node_affinity.required.node_selector_terms[0].match_expressions)
            == 1,
            len(
                pv.spec.node_affinity.required.node_selector_terms[0]
                .match_expressions[0]
                .values
            )
            == 1,
            pv.spec.node_affinity.required.node_selector_terms[0]
            .match_expressions[0]
            .key
            == "hostname",
            pv.spec.node_affinity.required.node_selector_terms[0]
            .match_expressions[0]
            .operator
            == "In",
            pv.spec.node_affinity.required.node_selector_terms[0].match_fields
            in (None, []),
        )
    )
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
    ctx = {
        "name": name,
        "namespace": CONFIG["namespace"],
        "nodeSelector": json.dumps({"kubernetes.io/hostname": node}),
        "cmd": json.dumps(fn),
        "image_repository": (
            f"{registry}/{repository}" if registry is not None else repository
        ),
        "image_tag": CONFIG["image_tag"],
        "datadir": CONFIG["node_datadir"],
        "log_format": log_format,
        "log_level": log_level,
    }
    template = Path("./templates/task.yaml").read_bytes().decode()
    manifest = template.format(**ctx)
    obj = yaml.safe_load(manifest)
    api.create_namespaced_pod(
        namespace=CONFIG["namespace"],
        body=obj,
    )

    def is_finished():
        task_pod = api.read_namespaced_pod(name=name, namespace=CONFIG["namespace"])
        status = task_pod.status
        if status.phase in ["Succeeded", "Failed"]:
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
        logger.error("run_on_node task failed", exit_code=exit_code, output=logs)
        raise CalledProcessError(returncode=exit_code, cmd=f"Task: {name}", output=logs)

    match = re.search(f"{VOLUME_IS_ATTACHED}=(True|False)", logs)
    is_attached = match.group(1) == "True" if match else None
    return is_attached

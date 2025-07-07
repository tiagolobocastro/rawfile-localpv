import json
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from time import sleep

import pykube
import re
import yaml
from datetime import datetime
from consts import CONFIG, VOLUME_IS_ATTACHED
from munch import Munch
from utils.logs import logger, format as log_format, level as log_level

api = pykube.HTTPClient(pykube.KubeConfig.from_env())


def volume_to_node(volume_id):
    pv = pykube.PersistentVolume.objects(api).get_by_name(name=volume_id)
    pv = Munch.fromDict(pv.obj)
    node_name = pv.spec.nodeAffinity.required.nodeSelectorTerms[0].matchExpressions[0][
        "values"
    ][0]
    expected_node_affinity = yaml.safe_load(
        f"""
required:
  nodeSelectorTerms:
  - matchExpressions:
    - key: hostname
      operator: In
      values:
      - {node_name}
    """
    )
    assert pv.spec.nodeAffinity == expected_node_affinity
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
        "reserved_storage": CONFIG["reserved_storage"],
    }
    template = Path("./templates/task.yaml").read_bytes().decode()
    manifest = template.format(**ctx)
    obj = yaml.safe_load(manifest)
    task_pod = pykube.Pod(api, obj)
    task_pod.create()

    def is_finished():
        task_pod.reload()
        status = task_pod.obj["status"]
        if status["phase"] in ["Succeeded", "Failed"]:
            return True
        return False

    wait_for(is_finished, "task to finish")
    logs = task_pod.logs()
    task_pod.delete()

    if task_pod.obj["status"]["phase"] != "Succeeded":
        exit_code = task_pod.obj["status"]["containerStatuses"][0]["state"][
            "terminated"
        ]["exitCode"]
        logger.error("run_on_node task failed", exit_code=exit_code, output=logs)
        raise CalledProcessError(returncode=exit_code, cmd=f"Task: {name}", output=logs)

    match = re.search(f"{VOLUME_IS_ATTACHED}=(True|False)", logs)
    is_attached = match.group(1) == "True" if match else None
    return is_attached

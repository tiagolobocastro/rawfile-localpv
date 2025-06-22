import logging
import os

import common

logger = logging.getLogger(__name__)


def deployer():
    return f"{common.root_dir()}/.ci/deployer.sh"


class Deployer:
    def __init__(self):
        self.reuse = reuse_cluster()

    def start(self):
        if self.reuse:
            return
        common.run(deployer(), ["start"])

    def stop(self):
        if self.reuse:
            return
        common.run(deployer(), ["stop"])


def reuse_cluster():
    reuse = os.getenv("REUSE_CLUSTER")
    # By default, we try to reuse
    if reuse is None or reuse.lower() in ("yes", "true", "y", "1"):
        cluster = common.run("kind", ["get", "clusters"], log_run=False)
        # todo: use config from ours, rather than allow only ours
        return cluster == "rawfile"
    return False

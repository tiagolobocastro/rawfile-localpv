import os
import importlib.metadata

PROVISIONER_NAME = os.getenv("PROVISIONER_NAME", "rawfile.csi.openebs.io")
PROVISIONER_VERSION = importlib.metadata.version("rawfile")
DATA_DIR = "/data"
CONFIG = {}
D_PERMS = 0o700
F_PERMS = 0o600
OWNER_UMASK = 0o077
RESOURCE_EXHAUSTED_EXIT_CODE = 101
VOLUME_IN_USE_EXIT_CODE = 102
VOLUME_IS_ATTACHED = "openebs.io/rawfile/is-attached"
FORMAT_OPTIONS_KEY = "openebs.io/rawfile/format-options"

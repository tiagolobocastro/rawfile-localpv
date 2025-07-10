import inspect
import base64
import pickle
import os

from consts import D_PERMS
from utils.lock import VolLock


class remote_fn(object):
    def __init__(self, fn):
        self.fn = fn

    def as_cmd(self, *args, **kwargs):
        call_data = [inspect.getsource(self.fn).encode(), args, kwargs]
        call_data_serialized = base64.b64encode(pickle.dumps(call_data))

        run_cmd = f"""
python <<EOF
import base64
import pickle
import os
from utils.logs import LoggingFormats, init as init_logging, logger
from consts import CONFIG

CONFIG["reserved_storage"] = int(os.getenv("RESERVED_STORAGE", "0"))
CONFIG["capacity_override"] = int(os.getenv("CAPACITY_OVERRIDE", "0"))

init_logging(LoggingFormats(os.getenv("LOG_FORMAT")), os.getenv("LOG_LEVEL"))
remote_fn = lambda fn: fn # FIXME: dirty hack
call_data = pickle.loads(base64.b64decode({call_data_serialized}))
exec(call_data[0])
{self.fn.__name__}(*call_data[1], **call_data[2])
EOF
        """
        return run_cmd

    def __call__(self, *args, **kwargs):
        raise Exception("Should only be run inside pod")


def scrub(volume_id):
    import time
    from subprocess import CalledProcessError

    import utils.rawfile
    from consts import VOLUME_IN_USE_EXIT_CODE

    img_dir = utils.rawfile.img_dir(volume_id)
    if not img_dir.exists():
        return

    img_file = utils.rawfile.img_file(volume_id)
    loops = utils.rawfile.attached_loops(img_file.resolve().as_posix())
    if len(loops) > 0:
        raise CalledProcessError(returncode=VOLUME_IN_USE_EXIT_CODE, cmd="")

    now = time.time()
    deleted_at = now
    gc_at = now  # TODO: GC sensitive PVCs later
    utils.rawfile.patch_metadata(volume_id, {"deleted_at": deleted_at, "gc_at": gc_at})
    utils.rawfile.gc_if_needed(volume_id, dry_run=False)


def init_rawfile(volume_id, size, thin_provision=False):
    import time
    from pathlib import Path
    from subprocess import CalledProcessError

    import utils.rawfile
    from consts import RESOURCE_EXHAUSTED_EXIT_CODE
    from volume_schema import LATEST_SCHEMA_VERSION

    if utils.rawfile.get_capacity() < size:
        raise CalledProcessError(returncode=RESOURCE_EXHAUSTED_EXIT_CODE, cmd="")

    img_dir = utils.rawfile.img_dir(volume_id)
    img_dir.mkdir(mode=D_PERMS, exist_ok=True)

    with VolLock(volume_id):
        img_file = Path(f"{img_dir}/disk.img")
        if img_file.exists() and os.path.getsize(img_file) >= size:
            return
        utils.rawfile.patch_metadata(
            volume_id,
            {
                "schema_version": LATEST_SCHEMA_VERSION,
                "volume_id": volume_id,
                "created_at": time.time(),
                "img_file": img_file.as_posix(),
                "size": size,
                "thin_provision": thin_provision,
            },
        )
        if thin_provision:
            utils.rawfile.truncate(img_file, size)
            return
        utils.rawfile.fallocate(img_file, size)


def get_capacity():
    import utils.rawfile

    cap = utils.rawfile.get_capacity()
    return max(0, cap)


def is_attached(volume_id):
    import utils.rawfile

    img_dir = utils.rawfile.img_dir(volume_id)
    if not img_dir.exists():
        return False

    img_file = utils.rawfile.img_file(volume_id)
    loops = utils.rawfile.attached_loops(img_file)
    return len(loops) > 0


def log_attached(volume_id):
    from consts import VOLUME_IS_ATTACHED
    from utils.logs import logger

    try:
        attached = is_attached(volume_id)
        logger.info("Volume attachment", **{VOLUME_IS_ATTACHED: attached})
        print(
            f"{VOLUME_IS_ATTACHED}={attached}"
        )  # We are using this output in `k8s.py`
    except Exception:
        # Failed to figure this out, keep old behavior
        logger.exception("Failed to check if volume was attached", volume_id=volume_id)
        pass


@remote_fn
def expand_rawfile(volume_id, size):
    import utils.rawfile
    from utils.remote import log_attached
    from utils.lock import VolLock
    from consts import RESOURCE_EXHAUSTED_EXIT_CODE

    with VolLock(volume_id):
        img_file = utils.rawfile.img_file(volume_id)
        size_inc = size - utils.rawfile.metadata(volume_id)["size"]
        if size_inc <= 0:
            log_attached(volume_id)
            return

        if utils.rawfile.get_capacity() < size_inc:
            exit(RESOURCE_EXHAUSTED_EXIT_CODE)
        if utils.rawfile.metadata(volume_id).get("thin_provision", False):
            utils.rawfile.truncate(img_file, size)
        else:
            utils.rawfile.fallocate(img_file, size)
        utils.rawfile.patch_metadata(
            volume_id,
            {"size": size},
        )
        log_attached(volume_id)

import os

from consts import D_PERMS
from utils.lock import VolLock


def scrub(volume_id) -> int:
    import time
    from subprocess import CalledProcessError

    import utils.rawfile
    from consts import VOLUME_IN_USE_EXIT_CODE

    img_dir = utils.rawfile.img_dir(volume_id)
    if not img_dir.exists():
        return 0

    img_file = utils.rawfile.img_file(volume_id)
    img_size = utils.rawfile.img_size(volume_id)
    loops = utils.rawfile.attached_loops(img_file.resolve().as_posix())
    if len(loops) > 0:
        raise CalledProcessError(returncode=VOLUME_IN_USE_EXIT_CODE, cmd="")

    now = time.time()
    deleted_at = now
    gc_at = now  # TODO: GC sensitive PVCs later
    utils.rawfile.patch_metadata(volume_id, {"deleted_at": deleted_at, "gc_at": gc_at})
    utils.rawfile.gc_if_needed(volume_id, dry_run=False)
    return img_size


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
    loops = utils.rawfile.attached_loops(img_file.as_posix())
    return len(loops) > 0

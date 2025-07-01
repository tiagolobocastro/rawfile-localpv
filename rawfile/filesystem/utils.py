import subprocess
from pathlib import Path
from utils.commands import run


def get_device_fs(device: str) -> str | None:
    res = run(f"blkid -o value -s TYPE {device}", capture_output=True, check=False)
    if res.returncode == 2:  # specified token was not found
        return None

    return res.stdout.decode().strip()


def get_device_for_mountpoint(mountpoint: str) -> str | None:
    try:
        output = run(
            f"mount | grep 'on {mountpoint}'",
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        return None
    lines = output.stdout.decode().strip().splitlines()
    if not len(lines):
        return None
    return Path(lines[0].split(" ")[0].strip()).resolve().as_posix()

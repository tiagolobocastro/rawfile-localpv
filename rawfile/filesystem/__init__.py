from enum import StrEnum
from .base import FileSystem as FileSystemBase
from .ext4 import EXT4
from .btrfs import BTRFS
from .xfs import XFS
from .utils import get_device_fs
from utils.rawfile import device_to_mountpoint
from collections import defaultdict
from consts import CONFIG


class FileSystemName(StrEnum):
    EXT4 = "ext4"
    BTRFS = "btrfs"
    XFS = "xfs"


filesystems: dict[FileSystemName | None, type[FileSystemBase]] = {
    FileSystemName.EXT4: EXT4,
    FileSystemName.BTRFS: BTRFS,
    FileSystemName.XFS: XFS,
}


def from_device(device: str) -> FileSystemBase | None:
    current_fs = get_device_fs(device)
    try:
        return filesystems[FileSystemName(current_fs)](
            device, device_to_mountpoint(device)
        )
    except (ValueError, KeyError):
        return None


def get_from_device_or_fallback(device: str, fallback: FileSystemName):
    """
    Attempts to get a filesystem instance from the device.
    If the filesystem is not recognized, it falls back to the specified filesystem type.

    Used to get filesystem instance by it's CSI parameters (For example user can recreate the same SC with diffrent filesystems).

    :param device: The device to check.
    :param fallback: The filesystem type to use if the device's filesystem is not recognized.
    :return: An instance of the filesystem or the fallback filesystem.
    """
    _filesystems = defaultdict(lambda: filesystems[CONFIG["default_fs"]])
    _filesystems.update(filesystems)
    return from_device(device) or _filesystems[fallback](
        device, device_to_mountpoint(device)
    )

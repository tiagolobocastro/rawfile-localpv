from .base import (
    FileSystem as FileSystemBase,
    FileSystemResizeError,
)
from utils.commands import run


class XFS(FileSystemBase):
    @property
    def __filesystem__(self) -> str:
        return "xfs"

    def resize(self) -> str:
        try:
            output = run(
                f"xfs_growfs -d {self.mountpoint}",
                check=True,
                capture_output=True,
            )
            return output.stdout.decode()
        except Exception as e:
            raise FileSystemResizeError.from_exc(e, self.__filesystem__)

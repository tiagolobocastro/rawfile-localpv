import fcntl
from utils.rawfile import lock_file

"""
  This can be used to ensure there's only 1 operation running at a time for a given volume.
"""


class VolLock:
    def __init__(self, volume_id):
        self.path = lock_file(volume_id)
        self.path.touch(exist_ok=True)
        self.file = open(self.path, "a")

    def __enter__(self):
        # grabs the lock or fails right away
        fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return self

    def release(self):
        if hasattr(self, "file"):
            fcntl.flock(self.file, fcntl.LOCK_UN)
            self.file.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

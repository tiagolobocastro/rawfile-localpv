class UnknownDeviceForMountpointError(ValueError):
    """
    Exception raised when we where unable to find the device for given mountpoint.
    """

    def __init__(self, mountpoint: str):
        self.mountpoint = mountpoint
        self.message = (
            f"Unable to determine the device for mountpoint '{self.mountpoint}'"
        )
        super().__init__(self.message)


class InvalidDeviceForMountpointError(ValueError):
    """
    Exception raised when device that is connected to mountpoint is not a correct device
    """

    def __init__(self, device: str, mountpoint: str):
        self.device = device
        self.mountpoint = mountpoint
        self.message = (
            f"Device {self.device} is not valid for mountpoint {self.mountpoint}"
        )
        super().__init__(self.message)


class SnapshotCreateVolumeInUse(Exception):
    """
    Exception raised when Snapshot is creating and volume is in use
    """

    def __init__(self, volume_id, snapshot_name):
        self.snapshot_name = snapshot_name
        self.volume_id = volume_id
        self.message = f"Unable to create snapshot for used volume, Volume '{self.volume_id}' and Snapshot '{self.snapshot_name}'"
        super().__init__(self.message)


class VolumeCloningNotSupported(NotImplementedError):
    """
    Exception raised when volume create requested cloning another volume
    """

    def __init__(self):
        self.message = "Volume Cloning is not supported"
        super().__init__(self.message)


class FsFreezeNotSupportedOnBlockVolumes(NotImplementedError):
    """
    Exception raised when fsfreeze is requested on block volume
    """

    def __init__(self):
        self.message = "FsFreeze is not supported on block volumes"
        super().__init__(self.message)

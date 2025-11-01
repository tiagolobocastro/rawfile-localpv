from utils.devices import path_stats
from utils.volume_manager import manager as volume_manager
from config import config
from consts import DATA_DIR


def get_capacity():
    disk_free_size = path_stats(DATA_DIR, config.capacity_override)["fs_avail"]
    capacity = disk_free_size
    for volume_stat in volume_manager.get_all_volumes_stats().values():
        capacity -= volume_stat["total"] - volume_stat["used"]
    if isinstance(config.reserved_capacity, str):
        capacity -= capacity * int(config.reserved_capacity[:-1]) / 100
    else:
        capacity -= config.reserved_capacity.to("B")
    return max(capacity, 0)

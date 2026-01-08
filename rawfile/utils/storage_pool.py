from utils.devices import path_stats
from utils.volume_manager import manager as volume_manager
from config import config


def get_capacity(storage_pool: str | None = None):
    if not storage_pool:
        storage_pool = config.csi_driver.default_pool
    pool = config.csi_driver.storage_pools[storage_pool]
    disk_free_size = path_stats(pool.path, pool.capacity_override)["fs_avail"]
    capacity = disk_free_size
    for volume_stat in volume_manager.get_all_volumes_stats().values():
        capacity -= volume_stat["total"] - volume_stat["used"]
    if isinstance(pool.reserved_capacity, str):
        capacity -= capacity * int(pool.reserved_capacity[:-1]) / 100
    else:
        capacity -= pool.reserved_capacity.to("B")
    return max(capacity, 0)

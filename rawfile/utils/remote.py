import utils.rawfile
import utils.storage_pool


def get_capacity(storage_pool: str | None = None):
    cap = utils.storage_pool.get_capacity(storage_pool)
    return max(0, cap)

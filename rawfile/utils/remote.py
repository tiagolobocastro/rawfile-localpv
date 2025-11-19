import utils.rawfile
import utils.storage_pool


def get_capacity():
    cap = utils.storage_pool.get_capacity()
    return max(0, cap)

from prometheus_client.core import REGISTRY
from prometheus_client.exposition import start_http_server
from prometheus_client.metrics_core import GaugeMetricFamily
from utils.storage_pool import get_capacity
from utils.volume_manager import manager as volume_manager


class VolumeStatsCollector(object):
    def __init__(self, node):
        self.node = node

    def collect(self):
        remaining_capacity = GaugeMetricFamily(
            "rawfile_remaining_capacity",
            "Free capacity for new volumes on this node (excluding reserved storage).",
            labels=["node"],
            unit="bytes",
        )
        volume_used = GaugeMetricFamily(
            "rawfile_volume_used",
            "Actual amount of disk used space by volume",
            labels=["node", "volume"],
            unit="bytes",
        )
        volume_total = GaugeMetricFamily(
            "rawfile_volume_total",
            "Amount of disk allocated to this volume",
            labels=["node", "volume"],
            unit="bytes",
        )
        remaining_capacity.add_metric([self.node], get_capacity())
        for volume_id, stats in volume_manager.get_all_volumes_stats().items():
            volume_used.add_metric([self.node, volume_id], stats["used"])
            volume_total.add_metric([self.node, volume_id], stats["total"])
        return [remaining_capacity, volume_used, volume_total]


def expose_metrics(node, port):
    REGISTRY.register(VolumeStatsCollector(node))
    start_http_server(port)

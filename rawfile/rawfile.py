#!/usr/bin/env python3
from concurrent import futures
import signal
import bd2fs
import click
import grpc
from filesystem import FileSystemName
import rawfile_servicer
from datetime import datetime
from consts import CONFIG
from csi import csi_pb2_grpc
from metrics import expose_metrics
from utils.rawfile import gc_all_volumes, migrate_all_volume_schemas
from utils.logs import LoggingFormats, init as init_logging, logger
from utils.units import pretty_size_to_bytes


@click.group()
@click.option("--image-registry", envvar="IMAGE_REGISTRY")
@click.option("--image-repository", envvar="IMAGE_REPOSITORY")
@click.option("--image-tag", envvar="IMAGE_TAG")
@click.option("--node-datadir", envvar="NODE_DATADIR")
@click.option("--namespace", envvar="NAMESPACE")
@click.option("--default-fs", envvar="DEFAULT_FS", default="ext4")
@click.option("--log-format", envvar="LOG_FORMAT", default=LoggingFormats.JSON)
@click.option("--log-level", envvar="LOG_LEVEL", default="INFO")
@click.option("--reserved-storage", envvar="RESERVED_STORAGE", default="0")
@click.option("--capacity-override", envvar="CAPACITY_OVERRIDE", default="0")
def cli(
    image_registry,
    image_repository,
    image_tag,
    node_datadir,
    namespace,
    default_fs,
    log_format,
    log_level,
    reserved_storage,
    capacity_override,
):
    CONFIG["image_registry"] = image_registry
    CONFIG["image_repository"] = image_repository
    CONFIG["image_tag"] = image_tag
    CONFIG["node_datadir"] = node_datadir
    CONFIG["namespace"] = namespace
    CONFIG["default_fs"] = FileSystemName(default_fs)
    if not reserved_storage.endswith("%"):
        CONFIG["reserved_storage"] = pretty_size_to_bytes(reserved_storage)
    else:
        CONFIG["reserved_storage"] = reserved_storage
    _capacity_override = pretty_size_to_bytes(capacity_override)
    if _capacity_override:
        CONFIG["capacity_override"] = _capacity_override
    init_logging(_format=LoggingFormats(log_format), _level=log_level)


@cli.command()
@click.option("--endpoint", envvar="CSI_ENDPOINT", default="0.0.0.0:5000")
@click.option("--nodeid", envvar="NODE_ID")
@click.option("--metrics-port", envvar="METRICS_PORT", default=9100)
@click.option(
    "--enable-metrics/--disable-metrics", envvar="ENABLE_METRICS", default=True
)
def csi_driver(endpoint, nodeid, enable_metrics, metrics_port):
    migrate_all_volume_schemas()
    if enable_metrics:
        expose_metrics(nodeid, metrics_port)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    csi_pb2_grpc.add_IdentityServicer_to_server(
        bd2fs.Bd2FsIdentityServicer(rawfile_servicer.RawFileIdentityServicer()), server
    )
    csi_pb2_grpc.add_NodeServicer_to_server(
        bd2fs.Bd2FsNodeServicer(rawfile_servicer.RawFileNodeServicer(node_name=nodeid)),
        server,
    )
    csi_pb2_grpc.add_ControllerServicer_to_server(
        bd2fs.Bd2FsControllerServicer(rawfile_servicer.RawFileControllerServicer()),
        server,
    )
    server.add_insecure_port(endpoint)

    def signal_handler(sig, _=None):
        grace_seconds = 20

        logger.info("Received termination request", signal=signal.Signals(sig).name)
        logger.info(
            "Stopping the CSI server with a grace period", grace_seconds=grace_seconds
        )

        start = datetime.now()
        server.stop(grace_seconds)
        end = datetime.now()
        elapsed = end - start

        logger.info("CSI Server has stopped", elapsed=elapsed, start=start, end=end)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    server.start()
    server.wait_for_termination()


@cli.command()
@click.option("--dry-run/--seriously", default=True)
def gc(dry_run):
    gc_all_volumes(dry_run=dry_run)


if __name__ == "__main__":
    cli()

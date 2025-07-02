#!/usr/bin/env python3
import logging
from concurrent import futures
import signal
import time
import bd2fs
import click
import grpc
from filesystem import FileSystemName
import rawfile_servicer
from consts import CONFIG
from csi import csi_pb2_grpc
from metrics import expose_metrics
from utils.rawfile import gc_all_volumes, migrate_all_volume_schemas
from utils.logs import LoggingFormats, init as init_logging


@click.group()
@click.option("--image-registry", envvar="IMAGE_REGISTRY")
@click.option("--image-repository", envvar="IMAGE_REPOSITORY")
@click.option("--image-tag", envvar="IMAGE_TAG")
@click.option("--node-datadir", envvar="NODE_DATADIR")
@click.option("--namespace", envvar="NAMESPACE")
@click.option("--default-fs", envvar="DEFAULT_FS", default="ext4")
@click.option("--log-format", envvar="LOG_FORMAT", default=LoggingFormats.JSON)
def cli(
    image_registry,
    image_repository,
    image_tag,
    node_datadir,
    namespace,
    default_fs,
    log_format,
):
    CONFIG["image_registry"] = image_registry
    CONFIG["image_repository"] = image_repository
    CONFIG["image_tag"] = image_tag
    CONFIG["node_datadir"] = node_datadir
    CONFIG["namespace"] = namespace
    CONFIG["default_fs"] = FileSystemName(default_fs)
    init_logging(LoggingFormats(log_format))


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

    def signal_handler(signum, frame: None):
        grace_seconds = 20

        print(f"Received termination request via signal: {signal.Signals(signum).name}")
        print(f"Stopping the CSI server with a grace period of {grace_seconds} seconds")

        start = time.time()
        server.stop(grace_seconds)
        elapsed = time.time() - start

        print(f"CSI Server has stopped after {elapsed:.1f} seconds")

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    server.start()
    server.wait_for_termination()


@cli.command()
@click.option("--dry-run/--seriously", default=True)
def gc(dry_run):
    gc_all_volumes(dry_run=dry_run)


if __name__ == "__main__":
    logging.basicConfig()
    cli()

#!/usr/bin/env python3
from concurrent import futures
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
import signal
import bd2fs
from config.model import CSIDriverCmd
import grpc
import rawfile_servicer
from datetime import datetime
from csi import csi_pb2_grpc
from internal import internal_pb2_grpc
from metrics import expose_metrics
from utils import task_manager
from utils.rawfile import is_cow_supported
from utils.logs import init as init_logging, logger
from internal_svc import InternalServicer, SignatureInterceptor
import consts
from analytics.ga4 import run_ping, shutdown_event_worker, run_event_worker
from orchestrator.k8s import node_ip_mapping
from utils.volume_manager import manager as volume_manager
import os


def node_driver_preflight_checks():
    data_dir = Path(consts.DATA_DIR)
    if not data_dir.exists():
        logger.info("Creating data directory", path=str(data_dir))
        data_dir.mkdir(parents=True, exist_ok=True)
    if not data_dir.is_dir():
        raise RuntimeError(f"{data_dir} is not a directory")
    if not os.access(data_dir, os.W_OK | os.R_OK | os.X_OK):
        raise RuntimeError(f"{data_dir} is not accessible")
    data_dir.chmod(consts.D_PERMS)
    volume_manager.migrate_all_volume_schemas()
    consts.COW_SUPPORTED = is_cow_supported(data_dir)


def csi_driver(driver_config: CSIDriverCmd):
    if driver_config.enable_metrics:
        expose_metrics(driver_config.nodeid, driver_config.metrics_port)

    if driver_config.plugin_type == "controller":
        run_ping()

    logger.debug(
        "Starting gRPC server",
        endpoint=driver_config.endpoint,
        nodeid=driver_config.nodeid,
        enable_metrics=driver_config.enable_metrics,
        plugin_type=driver_config.plugin_type,
    )
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=int(driver_config.grpc_workers))
    )
    bg_task_executor = ThreadPoolExecutor(max_workers=5)
    _task_manager = task_manager.TaskManager(bg_task_executor)
    internal_server = None
    csi_pb2_grpc.add_IdentityServicer_to_server(
        bd2fs.Bd2FsIdentityServicer(
            rawfile_servicer.RawFileIdentityServicer(),
        ),
        server,
    )
    if driver_config.plugin_type == "node":
        node_driver_preflight_checks()
        csi_pb2_grpc.add_NodeServicer_to_server(
            bd2fs.Bd2FsNodeServicer(
                rawfile_servicer.RawFileNodeServicer(node_name=driver_config.nodeid),
                task_manager=_task_manager,
            ),
            server,
        )
        run_event_worker()
        internal_server = grpc.server(
            futures.ThreadPoolExecutor(
                max_workers=int(driver_config.internal_grpc_workers)
            ),
            interceptors=[SignatureInterceptor(driver_config.internal_signature)],
        )
        internal_pb2_grpc.add_InternalServicer_to_server(
            InternalServicer(), internal_server
        )
        internal_server.add_insecure_port(
            f"{driver_config.internal_ip}:{driver_config.internal_port}"
        )

    # NOTE: Controller methods are exposed on node plugin too because we are using distributed-snapshotting
    # and Snapshotting methods are only available in Controller Service right now
    csi_pb2_grpc.add_ControllerServicer_to_server(
        bd2fs.Bd2FsControllerServicer(
            rawfile_servicer.RawFileControllerServicer(task_manager=_task_manager),
            task_manager=_task_manager,
        ),
        server,
    )
    server.add_insecure_port(str(driver_config.endpoint))

    def signal_handler(sig, _=None):
        grace_seconds = 20

        # shutdown analytics worker
        shutdown_event_worker()

        logger.info("Received termination request", signal=signal.Signals(sig).name)
        logger.info(
            "Stopping the CSI server with a grace period", grace_seconds=grace_seconds
        )

        start = datetime.now()
        server.stop(grace_seconds)
        if internal_server:
            internal_server.stop(grace_seconds)
        _task_manager.shutdown(grace_seconds)
        end = datetime.now()
        elapsed = end - start

        logger.info(
            "CSI Server has been stopped", elapsed=elapsed, start=start, end=end
        )
        logger.info("Stopping node plugin DS watcher")
        start = datetime.now()
        node_ip_mapping.stop()
        end = datetime.now()
        elapsed = end - start
        logger.info(
            "Node plugin DS watcher has been stopped",
            elapsed=elapsed,
            start=start,
            end=end,
        )

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    server.start()
    if internal_server:
        internal_server.start()
    with futures.ThreadPoolExecutor() as executor:
        terminations = [
            executor.submit(server.wait_for_termination),
        ]
        if internal_server:
            terminations.append(executor.submit(internal_server.wait_for_termination))
        futures.wait(terminations, return_when=futures.FIRST_COMPLETED)


if __name__ == "__main__":
    from config import config

    init_logging(_format=config.log_format, _level=config.log_level)
    if config.gc:
        volume_manager.gc_all_volumes(config.gc.dry_run)
    elif config.csi_driver:
        csi_driver(config.csi_driver)

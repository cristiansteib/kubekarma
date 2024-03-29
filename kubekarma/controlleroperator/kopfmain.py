from datetime import datetime
from typing import Any

import kopf
import logging

from kubekarma.controlleroperator.core.controllerengine import (
    ControllerEngine
)
from kubekarma.controlleroperator.config import config
from kubekarma.controlleroperator.core.testsuite.lifecyclehandler import \
    ControllerCRDLifecycleHandler
from kubekarma.controlleroperator.grpcservicers.server import build_grpc_server
from kubekarma.controlleroperator.kinds.networktestsuite import \
    NetworkTestSuite
from kubekarma.controlleroperator.httpserver import get_threaded_server
from kubernetes import client


logger = logging.getLogger()

# Configure the logger for the whole application
root_logger = logging.getLogger()
root_logger.setLevel(config.log_level)

controller_engine = ControllerEngine()
api_client = client.ApiClient()


# I need to share the memory space between the kopf process and the http server
# because the http server needs the __publisher instance to notify the results.
http_server_thread = get_threaded_server(
    http_host="0.0.0.0",
    controller_engine=controller_engine
)
grpc_server = build_grpc_server(
    "[::]:8080",
    controller_engine
)


@kopf.on.login()
def login(**kwargs):
    conn = kopf.login_via_client(**kwargs)
    global api_client
    api_client = client.ApiClient()
    return conn


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    # Events configuration
    settings.posting.level = config.log_level
    settings.posting.enabled = True
    settings.execution.max_workers = 8

    settings.watching.connect_timeout = 1 * 60
    settings.watching.server_timeout = 5 * 60
    settings.persistence.finalizer = config.API_GROUP + "/finalizer"
    # Peering configuration should be enabled for HA,
    #   but I need to figure out how to make it work with kopf
    #   setting the POD status ready condition to false when the
    #   operator is paused due the condition of the peering.
    # settings.peering.name = "kubekarma"
    # priority = random.randint(0, 32767)
    # settings.peering.priority = priority
    # settings.peering.stealth = True
    # settings.peering.mandatory = True


@kopf.on.startup()
def start_http_server(**kwargs):
    global grpc_server
    global http_server_thread
    global controller_engine
    http_server_thread.start()
    controller_engine.start()
    logger.info("Starting gRPC server...")
    grpc_server.start()


@kopf.on.cleanup()
def stop_results_receiver(**kwargs):
    logger.info(repr(kwargs))
    global grpc_server
    global http_server_thread
    logger.info("Stopping http server...")
    http_server_thread.stop()
    logger.info("Stopping gRPC server...")
    grpc_server.stop(0)
    logger.info("Stopping controller engine...")
    global controller_engine
    controller_engine.stop()
    logger.info("Goodbye! 👋")


@kopf.on.probe(id='now')
def get_current_timestamp(**kwargs: Any) -> str:
    return datetime.utcnow().isoformat()


# Register the NetworkKubekarmaTestSuite CRD
network_test_suite = NetworkTestSuite(
    controller_engine=controller_engine
)

args = (
    config.API_GROUP,
    config.API_VERSION,
    network_test_suite.api_plural
)

handlers = ControllerCRDLifecycleHandler(test_suite_kind=network_test_suite)
(kopf.on.create(*args)(handlers.handle_create))
(kopf.on.delete(*args)(handlers.handle_delete))
(kopf.on.resume(*args)(handlers.handle_resume_controller_restart)) # noqa
(kopf.on.field(
    *args,
    field='spec.suspend',
    # Avoid call this handler when the CRD is created
    when=lambda reason, **_: reason is not kopf.Reason.CREATE
)(handlers.handle_suspend)) # noqa
(kopf.on.update(*args)(handlers.handle_update))

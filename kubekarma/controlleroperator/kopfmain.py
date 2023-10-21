from datetime import datetime
from typing import Any

import kopf
import logging

from kubekarma.controlleroperator.core.controllerengine import (
    ControllerEngine
)
from kubekarma.controlleroperator.core.testsuite.testsuitekind import (
    TestSuiteKindBase
)
from kubekarma.controlleroperator.config import config
from kubekarma.controlleroperator.grpcsrv.server import build_grpc_server
from kubekarma.controlleroperator import get_results_publisher
from kubekarma.shared.crd.networktestsuite import NetworkTestSuiteCRD
from kubekarma.controlleroperator.httpserver import get_threaded_server
from kubernetes import client


logger = logging.getLogger(__name__)
api_client = client.ApiClient()

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

controller_engine = ControllerEngine()


class NetworkTestSuite(TestSuiteKindBase):
    kind = "NetworkTestSuite"
    api_plural = 'networktestsuites'
    crd_validator = NetworkTestSuiteCRD


crd_network_policy_tes_suite_handler = NetworkTestSuite(
    publisher=get_results_publisher(),
    controller_engine=controller_engine
)


# I need to share the memory space between the kopf process and the http server
# because the http server needs the publisher instance to notify the results.
http_server_thread = get_threaded_server(http_host="0.0.0.0")
grpc_server = build_grpc_server("[::]:8080")


@kopf.on.login()
def login(**kwargs):
    print(kwargs)
    conn = kopf.login_via_client(**kwargs)
    global api_client
    api_client = client.ApiClient()
    return conn


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    # settings.posting.level = logging.DEBUG
    # Events configuration
    settings.posting.level = logging.INFO
    settings.posting.enabled = True
    settings.execution.max_workers = 8
    settings.watching.connect_timeout = 1 * 60
    settings.watching.server_timeout = 5 * 60


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
    global http_server_thread
    global grpc_server
    http_server_thread.stop()
    logger.info("Stopping gRPC server...")
    grpc_server.stop(0)
    logger.info("Goodbye! 👋")


@kopf.on.probe(id='now')
def get_current_timestamp(**kwargs: Any) -> str:
    return datetime.utcnow().isoformat()


# Register the NetworkTestSuite CRD
args = (
    config.API_GROUP,
    config.API_VERSION,
    crd_network_policy_tes_suite_handler.api_plural
)

(kopf.on.create(*args)(crd_network_policy_tes_suite_handler.handle_create))
(kopf.on.update(*args)(crd_network_policy_tes_suite_handler.handle_update))
(kopf.on.delete(*args)(crd_network_policy_tes_suite_handler.handle_delete))
(kopf.on.resume(*args)(crd_network_policy_tes_suite_handler.handle_resume_controller_restart)) # noqa
(kopf.on.field(*args, field='spec.suspend')(crd_network_policy_tes_suite_handler.handle_suspend)) # noqa
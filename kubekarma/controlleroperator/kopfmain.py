import dataclasses
from datetime import datetime

import kopf
import logging

from kubekarma.controlleroperator.config import config
from kubekarma.controlleroperator.grpcsrv.server import build_grpc_server
from kubekarma.controlleroperator import get_results_publisher
from kubekarma.controlleroperator.handlers.networktestsuite import (
    NetworkTestSuiteHandler
)
from kubekarma.controlleroperator.httpserver import get_threaded_server
from kubernetes import client


logger = logging.getLogger(__name__)
api_client = client.ApiClient()

publisher = get_results_publisher()

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)


crd_network_policy_tes_suite_handler = NetworkTestSuiteHandler(
    publisher=publisher
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
    http_server_thread.start()
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
def get_current_timestamp(**kwargs):
    return datetime.utcnow().isoformat()


@dataclasses.dataclass
class ApiVersion:
    group: str
    version: str


def parse_api_version(api_version: str) -> ApiVersion:
    group, version = api_version.split('/')
    return ApiVersion(group=group, version=version)


(kopf.on.create(
    config.API_GROUP,
    config.API_VERSION,
    crd_network_policy_tes_suite_handler.API_PLURAL
)(crd_network_policy_tes_suite_handler.handle))


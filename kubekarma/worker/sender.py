import logging

import grpc
import urllib3

from kubekarma.shared.pb2 import controller_pb2_grpc, controller_pb2


class ControllerNotAvailable(Exception):
    ...


logger = logging.getLogger(__name__)


class ControllerCommunication:

    def __init__(self, controller_address: str):
        timeout = urllib3.Timeout(connect=2.0, read=5.0)
        self.http = urllib3.PoolManager(timeout=timeout)
        logger.info("connecting to controller at %s", controller_address)
        self.channel = grpc.insecure_channel(controller_address)
        self.controller = controller_pb2_grpc.ControllerServiceStub(
            self.channel
        )

    def send_results(
        self,
        results: controller_pb2.ProcessTestSuiteResultsRequest
    ):
        """Send the results of a task execution to the controller."""
        self.controller.ProcessTestSuiteResults(results)

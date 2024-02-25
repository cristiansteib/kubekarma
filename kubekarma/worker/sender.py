import logging

import grpc

from kubekarma.grpcgen.collectors.v1alpha import controller_pb2, \
    controller_pb2_grpc


class ControllerNotAvailable(Exception):
    ...


logger = logging.getLogger(__name__)


class ControllerCommunication:

    def __init__(self, controller_address: str):
        logger.info(
            "Connecting to controller at %s",
            controller_address
        )
        self.channel = grpc.insecure_channel(controller_address)
        self.controller = controller_pb2_grpc.TestSuiteExecutionResultServiceStub(
            self.channel
        )

    def send_results(
        self,
        results: controller_pb2.ExecutionResultRequest
    ):
        """Send the results of a task execution to the controller."""
        self.controller.ReportResults(results)

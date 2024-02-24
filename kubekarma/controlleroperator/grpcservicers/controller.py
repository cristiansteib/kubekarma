import grpc

from kubekarma.controlleroperator.core.abc.resultspublisher import \
    ITestResultsPublisher
from kubekarma.grpcgen.collectors.v1 import controller_pb2, \
    controller_pb2_grpc


class ControllerServiceServicer(controller_pb2_grpc.ControllerServiceServicer):

    def __init__(self, result_publisher: ITestResultsPublisher):
        self.result_publisher = result_publisher

    def ProcessTestSuiteResults(
        self,
        request: controller_pb2.ProcessTestSuiteResultsRequest,
        context: grpc.ServicerContext
    ):
        self.result_publisher.notify_new_results(
            request.token,
            results=request
        )
        return controller_pb2.ProcessTestSuiteResultsResponse(
            message="ok"
        )

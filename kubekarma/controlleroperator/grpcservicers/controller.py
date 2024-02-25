import grpc

from kubekarma.controlleroperator.core.abc.resultspublisher import \
    ITestResultsPublisher
from kubekarma.grpcgen.collectors.v1alpha import controller_pb2, \
    controller_pb2_grpc


class ControllerServiceServicer(
    controller_pb2_grpc.TestSuiteExecutionResultServiceServicer
):

    def __init__(self, result_publisher: ITestResultsPublisher):
        self.result_publisher = result_publisher

    def ReportResults(
        self,
        request: controller_pb2.ExecutionResultRequest,
        context: grpc.ServicerContext
    ):
        self.result_publisher.notify_new_results(
            request.token,
            results=request
        )
        return controller_pb2.ExecutionResultResponse(
            message="ok"
        )

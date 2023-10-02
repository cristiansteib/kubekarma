from kubekarma.controlleroperator import get_results_publisher
from kubekarma.shared.pb2 import controller_pb2_grpc, controller_pb2


class ControllerServiceServicer(controller_pb2_grpc.ControllerServiceServicer):

    def ProcessTestSuiteResults(
        self,
        request: controller_pb2.ProcessTestSuiteResultsRequest,
        context
    ):
        get_results_publisher().notify_new_results(
            request.token,
            results=request
        )
        return controller_pb2.ProcessTestSuiteResultsResponse(
            message="ok"
        )

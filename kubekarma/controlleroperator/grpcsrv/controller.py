from kubekarma.shared.pb2 import controller_pb2_grpc, controller_pb2


class ControllerServiceServicer(controller_pb2_grpc.ControllerServiceServicer):

    def ProcessTestSuiteResults(
        self,
        request: controller_pb2.ProcessTestSuiteResultsRequest,
        context
    ):
        # context.set_code(grpcsrv.StatusCode.UNIMPLEMENTED)
        # context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')
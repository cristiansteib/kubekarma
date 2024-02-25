import grpc
from kubekarma.controlleroperator.core.controllerengine import ControllerEngine
from kubekarma.controlleroperator.grpcservicers.controller import \
    ControllerServiceServicer
from kubekarma.controlleroperator.grpcservicers.health import HealthServicer
from kubekarma.grpcgen.collectors.v1alpha import controller_pb2_grpc
from kubekarma.grpcgen.health.v1 import health_pb2_grpc


def add_all_servicers_to_server(
    server,
    controller_engine: ControllerEngine
) -> grpc.Server:
    """Add all servicers into the server."""
    health_pb2_grpc.add_HealthServicer_to_server(
        HealthServicer(),
        server
    )
    controller_pb2_grpc.add_TestSuiteExecutionResultServiceServicer_to_server(
        ControllerServiceServicer(
            result_publisher=controller_engine.get_results_publisher()
        ),
        server
    )
    return server

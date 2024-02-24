import grpc
from concurrent import futures

from kubekarma.controlleroperator.core.controllerengine import ControllerEngine
from kubekarma.controlleroperator.grpcservicers.utils import \
    add_all_servicers_to_server


def build_grpc_server(
    server_address,
    controller_engine: ControllerEngine
) -> grpc.Server:
    """Return the gRPC server for the Master service."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_all_servicers_to_server(server, controller_engine)
    server.add_insecure_port(server_address)
    return server

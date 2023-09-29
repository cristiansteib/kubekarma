from concurrent import futures

import grpc

from kubekarma.controlleroperator.grpc.health import HealthServicer
from kubekarma.controlleroperator.grpc.pb2 import health_pb2_grpc


def build_grpc_server(server_address) -> grpc.Server:
    """Return the gRPC server for the Master service."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    health_pb2_grpc.add_HealthServicer_to_server(HealthServicer(), server)
    server.add_insecure_port(server_address)
    return server

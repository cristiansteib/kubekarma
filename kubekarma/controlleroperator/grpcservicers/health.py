import logging

from kubekarma.grpcgen.health.v1 import health_pb2_grpc
from kubekarma.grpcgen.health.v1.health_pb2 import HealthCheckResponse

logger = logging.getLogger(__name__)


class HealthServicer(health_pb2_grpc.HealthServicer):

    def __init__(self):
        self.__status = HealthCheckResponse.SERVING

    def set_status(self, status):
        self.__status = status

    def Check(self, request, context):
        logger.debug("Health check request received.")
        return HealthCheckResponse(status=self.__status)

    def Watch(self, request, context):
        logger.debug("Health watch request received.")
        return HealthCheckResponse(status=self.__status)

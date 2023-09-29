
class HealthzServicer(health_pb2_grpc.HealthServicer):

    def __init__(self):
        self.__status = health_pb2.HealthCheckResponse.SERVING

    def set_status(self, status):
        self.__status = status

    def Check(self, request, context):
        logger.debug("Health check request received.")
        return health_pb2.HealthCheckResponse(status=self.__status)
import logging
import os


class Envs:
    EXPOSED_CONTROLLER_GRPC_ADDRESS = 'EXPOSED_CONTROLLER_GRPC_ADDRESS'
    WORKER_DOCKER_IMAGE = 'WORKER_DOCKER_IMAGE'
    LOG_LEVEL = 'LOG_LEVEL'

    def get_exposed_controller_grpc_address(self) -> str:
        return os.getenv(self.EXPOSED_CONTROLLER_GRPC_ADDRESS)

    def get_worker_docker_image(self) -> str:
        return os.getenv(self.WORKER_DOCKER_IMAGE)

    def get_log_level(self) -> int:
        """Return the log level.

        possible values:
            CRITICAL:
            ERROR:
            WARNING
            INFO
            DEBUG
            NOTSET
        """
        return logging.getLevelName(
            os.getenv(self.LOG_LEVEL, 'INFO').upper()
        )
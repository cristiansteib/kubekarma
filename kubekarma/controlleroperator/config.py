import dataclasses
import os


@dataclasses.dataclass
class Config:
    controller_server_host: str
    worker_image: str
    API_GROUP = 'kubekarma.io'
    API_VERSION = 'v1'

    @classmethod
    def from_env_vars(cls) -> 'Config':
        return cls(
            controller_server_host=os.getenv("EXPOSED_CONTROLLER_GRPC_ADDRESS"),
            worker_image=os.getenv("WORKER_DOCKER_IMAGE")
        )


config = Config.from_env_vars()

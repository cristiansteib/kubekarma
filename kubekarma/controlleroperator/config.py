import dataclasses
import os


@dataclasses.dataclass
class Config:
    controller_server_host: str
    worker_image: str

    @classmethod
    def from_env_vars(cls) -> 'Config':
        return cls(
            controller_server_host=os.getenv("OPERATOR_SVC_HOST"),
            worker_image=os.getenv("WORKER_DOCKER_IMAGE")
        )


config = Config.from_env_vars()

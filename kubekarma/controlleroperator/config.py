import dataclasses
from kubekarma.controlleroperator import envs as _envs


@dataclasses.dataclass
class Config:
    controller_server_host: str
    worker_image: str
    log_level: int
    API_GROUP = 'kubekarma.io'
    API_VERSION = 'v1'

    @classmethod
    def from_env_vars(cls) -> 'Config':
        envs = _envs.Envs()
        return cls(
            controller_server_host=envs.get_exposed_controller_grpc_address(),
            worker_image=envs.get_worker_docker_image(),
            log_level=envs.get_log_level(),
        )


config = Config.from_env_vars()

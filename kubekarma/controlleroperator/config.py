import dataclasses
import os


@dataclasses.dataclass
class Config:
    controller_server_host: str

    @classmethod
    def from_env_vars(cls) -> 'Config':
        return cls(
            controller_server_host=os.getenv("OPERATOR_SVC_HOST"),
        )


config = Config.from_env_vars()

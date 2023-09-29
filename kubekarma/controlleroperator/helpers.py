import dataclasses

from kubekarma.controlleroperator.config import config


@dataclasses.dataclass
class AnnotationType:
    key: str
    value: str

    def to_kv(self) -> dict:
        return {self.key: self.value}


def generate_custom_annotation(
    key: str,
    value: str
) -> AnnotationType:
    """Generate a custom annotation for kubekarma.io."""
    return AnnotationType(
        f"{config.API_GROUP}/{key}",
        value
    )



import abc
from typing import List

from kubekarma.controlleroperator.core.abc.crdvalidator import ICrdValidator


class ControllerCRDValidator(abc.ABC):
    """A validator for the spec of the CRD."""

    def __init__(self, validator: ICrdValidator):
        self.validator = validator

    def validate(self, spec) -> List[str]:
        """Perform validations on the spec of the CRD.

        If detects any error it will raise an exception and change the status
        of the CRD to Failed.
        """
        assert isinstance(self.validator, ICrdValidator), (
            f"{self.validator} is not an instance of {ICrdValidator}"
        )
        return self.validator.validate_spec(spec)

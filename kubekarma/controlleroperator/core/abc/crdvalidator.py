import abc
from typing import List


class ICrdValidator(abc.ABC):

    @abc.abstractmethod
    def validate_spec(self, spec) -> List[str]:
        """Perform validations on the spec of the CRD."""

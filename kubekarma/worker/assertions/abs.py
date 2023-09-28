import abc
import dataclasses


@dataclasses.dataclass
class AssertionResult:
    """The result of an assertion."""
    used_clazz_name_fqn: str
    name: str
    success: bool
    message: str = None


class IAssertion(abc.ABC):

    @abc.abstractmethod
    def test(self) -> AssertionResult:
        """Run the assertion and return the results."""

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, d: dict):
        ...

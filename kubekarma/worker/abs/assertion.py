import abc

from kubekarma.worker.abs.exception import AssertionFailure


class IAssertion(abc.ABC):

    @abc.abstractmethod
    def test(self):
        """Run the assertion and return the results."""

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, d: dict) -> 'IAssertion':
        ...

    def raise_assertion_failure(self, message: str):
        raise AssertionFailure(
            self.__class__.__name__,
            message
        )

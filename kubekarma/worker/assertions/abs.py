import abc


class IAssertion(abc.ABC):

    @abc.abstractmethod
    def test(self):
        ...

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, d: dict):
        ...

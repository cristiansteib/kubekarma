import abc
from typing import List


class IKubekarmaTest(abc.ABC):

        @property
        @abc.abstractmethod
        def name(self) -> str:
            pass


class IKubekarmaTestSuite(abc.ABC):


        @property
        @abc.abstractmethod
        def kind(self) -> str:
            """The Kubernetes kind of test suite."""


        @property
        @abc.abstractmethod
        def name(self) -> str:
            pass

        @property
        @abc.abstractmethod
        def test_cases(self) -> List[IKubekarmaTest]:
            pass

        @abc.abstractmethod
        def execute_test(self, test_case: IKubekarmaTest):
            """Execute a test case.

            Raises:
                AssertionFailure: If the test case fails.
                NotImplementedError: If the test case is not implemented.
                Exception: If an unexpected error occurs.
            """

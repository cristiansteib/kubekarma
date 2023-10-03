"""A module to represent the generic CRD object status."""
import enum

from kubekarma.shared.pb2 import controller_pb2


class CRDTestPhase(enum.Enum):
    """The phase of a Test CRD object."""
    Pending = "Pending"
    Active = "Active"
    Failed = "Failed"
    Suspended = "Suspended"


class CRDTestExecutionStatus(enum.Enum):
    """Overall status of the test execution."""
    Pending = "Pending"
    Succeeding = "Succeeding"
    Failing = "Failing"


class TestCaseStatus(enum.Enum):
    """The status of a specific test case assert."""
    Failed = "Failed"
    Succeeded = "Succeeded"
    NotImplemented = "NotImplemented"
    Error = "Error"

    @classmethod
    def from_pb2_test_status(
        cls,
        status: controller_pb2.TestStatus
    ) -> 'TestCaseStatus':
        """Return the test case status defined by the CRD.

        This method converts the status transmitted by worker to the
        controller to the status defined by the CRD.
        """
        if status == controller_pb2.TestStatus.SUCCEEDED:
            return TestCaseStatus.Succeeded
        elif status == controller_pb2.TestStatus.FAILED:
            return TestCaseStatus.Failed
        elif status == controller_pb2.TestStatus.NOTIMPLEMENTED:
            return TestCaseStatus.NotImplemented
        elif status == controller_pb2.TestStatus.ERROR:
            return TestCaseStatus.Error
        else:
            raise Exception(f"Unknown status: {status}")
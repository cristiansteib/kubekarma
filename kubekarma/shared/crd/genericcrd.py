"""A module to represent the generic CRD object status."""
import enum

from kubekarma.grpcgen.collectors.v1 import controller_pb2


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


class AssertValidationStatus(enum.Enum):
    """The status of a specific test case assert."""
    Failed = "Failed"
    Succeeded = "Succeeded"
    NotImplemented = "NotImplemented"
    Error = "Error"

    @classmethod
    def from_pb2_test_status(
        cls,
        status: controller_pb2.TestCaseResult.TestStatus
    ) -> 'AssertValidationStatus':
        """Return the test case status defined by the CRD.

        This method converts the status transmitted by worker to the
        controller to the status defined by the CRD.
        """
        if status == controller_pb2.TestCaseResult.TestStatus.SUCCEEDED:
            return AssertValidationStatus.Succeeded
        elif status == controller_pb2.TestCaseResult.TestStatus.FAILED:
            return AssertValidationStatus.Failed
        elif status == controller_pb2.TestCaseResult.TestStatus.NOTIMPLEMENTED:
            return AssertValidationStatus.NotImplemented
        elif status == controller_pb2.TestCaseResult.TestStatus.ERROR:
            return AssertValidationStatus.Error
        else:
            raise Exception(f"Unknown status: {status}")

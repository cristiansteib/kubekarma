"""A module to represent the generic CRD object status."""
import enum


class CRDTestPhase(enum.Enum):
    """The phase of a Test CRD object."""
    Pending = "Pending"
    Created = "Created"
    Failed = "Failed"
    Suspended = "Suspended"


class CRDTestExecutionStatus(enum.Enum):
    """The execution status of a Test CRD object."""
    Pending = "Pending"
    Succeeding = "Succeeding"
    Failing = "Failing"


class TestCaseStatus(enum.Enum):
    """The status of a specific test case assert."""
    Failed = "Failed"
    Succeeded = "Succeeded"
    NotImplemented = "NotImplemented"
    Error = "Error"

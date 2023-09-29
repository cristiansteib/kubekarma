"""A module to represent the generic CRD object status."""
import dataclasses
import enum
from typing import Optional


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


@dataclasses.dataclass
class ExceptionCause:
    message: str
    file_name: str
    line_number: int
    function_name: str
    exception_type: str

    @classmethod
    def from_exception(cls, exception: Exception) -> "ExceptionCause":
        """Create an instance from an exception."""
        a_traceback = exception.__traceback__
        return cls(
            message=str(exception),
            file_name=a_traceback.tb_frame.f_code.co_filename if a_traceback else None,
            line_number=a_traceback.tb_lineno if a_traceback else None,
            function_name=a_traceback.tb_frame.f_code.co_name if a_traceback else None,
            exception_type=type(exception).__name__
        )

    def to_string(self) -> str:
        """Convert the exception to a string."""
        return (
            f"{self.exception_type}: {self.message}\n"
            f"  File \"{self.file_name}\", line {self.line_number}, in {self.function_name}"
        )


class TestCaseStatus(enum.Enum):
    """The status of a specific test case assert."""
    Failed = "Failed"
    Succeeded = "Succeeded"
    NotImplemented = "NotImplemented"
    Error = "Error"


@dataclasses.dataclass
class TestCaseResultItem:
    """The result of a specific test case assert."""
    name: str
    status: TestCaseStatus
    executionTime: str
    # time in timestamp format
    lastExecutionTime: str
    error: Optional[ExceptionCause] = None

    def __post_init__(self):
        if type(self.status) is str:
            self.status = TestCaseStatus(self.status)

        error = self.error
        if isinstance(error, dict):
            self.error = ExceptionCause(**error)

    def set_exception(self, exception: Exception):
        """Set the exception and extract the cause."""
        self.error = ExceptionCause.from_exception(exception)

    def to_safe_dict(self) -> dict:
        """A dict that is able to be serialized to JSON."""
        data = dataclasses.asdict(self)
        if data["error"]:
            data["error"] = self.error.to_string()
        data["status"] = data["status"].value
        return data

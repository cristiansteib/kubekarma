import dataclasses
import enum
import json
from typing import Optional


@dataclasses.dataclass
class ExecutionTaskConfig:
    identifier: str
    controller_version: str
    # NetworkPolicyTestSuite config spec
    np_test_suite_spec: dict


@dataclasses.dataclass
class ExceptionCause:
    message: str
    file_name: str
    line_number: int
    function_name: str
    exception_type: str


class TestCaseStatus(enum.Enum):
    Failed = "Failed"
    Success = "Success"
    NotImplemented = "NotImplemented"
    Error = "Error"


@dataclasses.dataclass
class TestResults:
    name: str
    status: TestCaseStatus
    executionTime: str
    error: Optional[ExceptionCause] = None

    def __post_init__(self):
        if type(self.status) is str:
            self.status = TestCaseStatus(self.status)

        error = self.error
        if isinstance(error, dict):
            self.error = ExceptionCause(**error)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "executionTime": self.executionTime,
            "error": self.error
        }

    def set_exception(self, exception: Exception):
        """Set the exception and extract the cause."""
        a_traceback = exception.__traceback__
        self.status = TestCaseStatus.Error
        self.error = ExceptionCause(
            message=str(exception),
            file_name=a_traceback.tb_frame.f_code.co_filename if a_traceback else None,
            line_number=a_traceback.tb_lineno if a_traceback else None,
            function_name=a_traceback.tb_frame.f_code.co_name if a_traceback else None,
            exception_type=type(exception).__name__
        )

    def to_safe_dict(self) -> dict:
        """A dict that is able to be serialized to JSON."""
        data = self.to_dict()
        if data["error"]:
            data["error"] = dataclasses.asdict(data["error"])
        return data



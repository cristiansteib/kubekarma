import dataclasses
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


@dataclasses.dataclass
class TestResults:
    name: str
    passed: bool
    message: str
    exception: Optional[ExceptionCause] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "exception": self.exception
        }

    def set_exception(self, exception: Exception):
        """Set the exception and extract the cause."""
        a_traceback = exception.__traceback__
        self.exception = ExceptionCause(
            message=str(exception),
            file_name=a_traceback.tb_frame.f_code.co_filename if a_traceback else None,
            line_number=a_traceback.tb_lineno if a_traceback else None,
            function_name=a_traceback.tb_frame.f_code.co_name if a_traceback else None,
            exception_type=type(exception).__name__
        )

    def to_safe_dict(self) -> dict:
        """A dict that is able to be serialized to JSON."""
        data = self.to_dict()
        if data["exception"]:
            data["exception"] = dataclasses.asdict(data["exception"])
        return data



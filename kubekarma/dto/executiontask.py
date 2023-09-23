import dataclasses
from typing import Optional


@dataclasses.dataclass
class ExecutionTaskConfig:
    identifier: str
    controller_version: str
    # NetworkPolicyTestSuite config spec
    np_test_suite_spec: dict


@dataclasses.dataclass
class ExecutionTaskReport:
    identifier: str
    status: str
    message: str


@dataclasses.dataclass
class TestResults:
    name: str
    passed: bool
    message: str
    exception: Optional[Exception]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "exception": self.exception
        }

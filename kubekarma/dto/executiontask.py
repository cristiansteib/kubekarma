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

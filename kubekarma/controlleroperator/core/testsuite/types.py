from typing import Optional, TypedDict


class TestSuiteStatusType(TypedDict):
    lastExecutionTime: str
    lastExecutionErrorTime: str
    lastSucceededTime: str
    testExecutionStatus: str
    testCases: list[dict]
    # passing: (Succeeded)/(Total)
    passingCount: str
    suspended: bool


class TestCaseStatusType(TypedDict):
    name: str
    status: str
    executionTime: str
    error: Optional[str]

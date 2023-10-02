from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TestStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    ERROR: _ClassVar[TestStatus]
    SUCCEEDED: _ClassVar[TestStatus]
    FAILED: _ClassVar[TestStatus]
    NOTIMPLEMENTED: _ClassVar[TestStatus]
ERROR: TestStatus
SUCCEEDED: TestStatus
FAILED: TestStatus
NOTIMPLEMENTED: TestStatus

class TestCaseResult(_message.Message):
    __slots__ = ["name", "status", "execution_duration", "execution_start_time", "error_message"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_DURATION_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_START_TIME_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    name: str
    status: TestStatus
    execution_duration: str
    execution_start_time: str
    error_message: str
    def __init__(self, name: _Optional[str] = ..., status: _Optional[_Union[TestStatus, str]] = ..., execution_duration: _Optional[str] = ..., execution_start_time: _Optional[str] = ..., error_message: _Optional[str] = ...) -> None: ...

class ProcessTestSuiteResultsRequest(_message.Message):
    __slots__ = ["name", "started_at_time", "test_case_results", "token"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    STARTED_AT_TIME_FIELD_NUMBER: _ClassVar[int]
    TEST_CASE_RESULTS_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    name: str
    started_at_time: str
    test_case_results: _containers.RepeatedCompositeFieldContainer[TestCaseResult]
    token: str
    def __init__(self, name: _Optional[str] = ..., started_at_time: _Optional[str] = ..., test_case_results: _Optional[_Iterable[_Union[TestCaseResult, _Mapping]]] = ..., token: _Optional[str] = ...) -> None: ...

class ProcessTestSuiteResultsResponse(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

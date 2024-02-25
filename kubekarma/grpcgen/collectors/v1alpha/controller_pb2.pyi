"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.duration_pb2
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.timestamp_pb2
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing_extensions.final
class ValidationResult(google.protobuf.message.Message):
    """*
    TestValidationResult represents a single test case result
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    class _Status:
        ValueType = typing.NewType("ValueType", builtins.int)
        V: typing_extensions.TypeAlias = ValueType

    class _StatusEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[ValidationResult._Status.ValueType], builtins.type):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        ERROR: ValidationResult._Status.ValueType  # 0
        """ERROR: when some exception was raised during the execution of the test case"""
        SUCCEEDED: ValidationResult._Status.ValueType  # 1
        """SUCCEEDED: when the test case was executed successfully"""
        FAILED: ValidationResult._Status.ValueType  # 2
        """FAILED: when the test case was executed but the assertion failed"""
        NOT_IMPLEMENTED: ValidationResult._Status.ValueType  # 3
        """NOTIMPLEMENTED: when the test case code is not implemented yet"""

    class Status(_Status, metaclass=_StatusEnumTypeWrapper): ...
    ERROR: ValidationResult.Status.ValueType  # 0
    """ERROR: when some exception was raised during the execution of the test case"""
    SUCCEEDED: ValidationResult.Status.ValueType  # 1
    """SUCCEEDED: when the test case was executed successfully"""
    FAILED: ValidationResult.Status.ValueType  # 2
    """FAILED: when the test case was executed but the assertion failed"""
    NOT_IMPLEMENTED: ValidationResult.Status.ValueType  # 3
    """NOTIMPLEMENTED: when the test case code is not implemented yet"""

    NAME_FIELD_NUMBER: builtins.int
    STATUS_FIELD_NUMBER: builtins.int
    DURATION_FIELD_NUMBER: builtins.int
    START_TIME_FIELD_NUMBER: builtins.int
    ERROR_MESSAGE_FIELD_NUMBER: builtins.int
    name: builtins.str
    """The specific name of the test case"""
    status: global___ValidationResult.Status.ValueType
    @property
    def duration(self) -> google.protobuf.duration_pb2.Duration:
        """How long it took to execute the test case"""
    @property
    def start_time(self) -> google.protobuf.timestamp_pb2.Timestamp:
        """When the test case started executing"""
    error_message: builtins.str
    """errorMessage is only set when the status is ERROR and it contains the
    exception message and stack trace
    """
    def __init__(
        self,
        *,
        name: builtins.str = ...,
        status: global___ValidationResult.Status.ValueType = ...,
        duration: google.protobuf.duration_pb2.Duration | None = ...,
        start_time: google.protobuf.timestamp_pb2.Timestamp | None = ...,
        error_message: builtins.str = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["duration", b"duration", "start_time", b"start_time"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["duration", b"duration", "error_message", b"error_message", "name", b"name", "start_time", b"start_time", "status", b"status"]) -> None: ...

global___ValidationResult = ValidationResult

@typing_extensions.final
class ExecutionResultRequest(google.protobuf.message.Message):
    """*
    TestSuiteResult represents the result of a whole test suite execution
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    NAME_FIELD_NUMBER: builtins.int
    START_TIME_FIELD_NUMBER: builtins.int
    VALIDATION_RESULTS_FIELD_NUMBER: builtins.int
    TOKEN_FIELD_NUMBER: builtins.int
    name: builtins.str
    """name: is the name of the test suite"""
    @property
    def start_time(self) -> google.protobuf.timestamp_pb2.Timestamp:
        """the time when the test suite started executing
        it should be in ISO 8601 format
        """
    @property
    def validation_results(self) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[global___ValidationResult]: ...
    token: builtins.str
    """token: is used to identify the test suite execution"""
    def __init__(
        self,
        *,
        name: builtins.str = ...,
        start_time: google.protobuf.timestamp_pb2.Timestamp | None = ...,
        validation_results: collections.abc.Iterable[global___ValidationResult] | None = ...,
        token: builtins.str = ...,
    ) -> None: ...
    def HasField(self, field_name: typing_extensions.Literal["start_time", b"start_time"]) -> builtins.bool: ...
    def ClearField(self, field_name: typing_extensions.Literal["name", b"name", "start_time", b"start_time", "token", b"token", "validation_results", b"validation_results"]) -> None: ...

global___ExecutionResultRequest = ExecutionResultRequest

@typing_extensions.final
class ExecutionResultResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    MESSAGE_FIELD_NUMBER: builtins.int
    message: builtins.str
    def __init__(
        self,
        *,
        message: builtins.str = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["message", b"message"]) -> None: ...

global___ExecutionResultResponse = ExecutionResultResponse

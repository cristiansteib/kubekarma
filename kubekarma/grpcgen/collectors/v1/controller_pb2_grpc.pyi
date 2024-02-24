"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import abc
import collections.abc
import grpc
import grpc.aio
import kubekarma.grpcgen.collectors.v1.controller_pb2
import typing

_T = typing.TypeVar('_T')

class _MaybeAsyncIterator(collections.abc.AsyncIterator[_T], collections.abc.Iterator[_T], metaclass=abc.ABCMeta):
    ...

class _ServicerContext(grpc.ServicerContext, grpc.aio.ServicerContext):  # type: ignore
    ...

class ControllerServiceStub:
    def __init__(self, channel: typing.Union[grpc.Channel, grpc.aio.Channel]) -> None: ...
    ProcessTestSuiteResults: grpc.UnaryUnaryMultiCallable[
        kubekarma.grpcgen.collectors.v1.controller_pb2.ProcessTestSuiteResultsRequest,
        kubekarma.grpcgen.collectors.v1.controller_pb2.ProcessTestSuiteResultsResponse,
    ]
    """ProcessTestSuiteResults is called by the test runner to report the results of the execution"""

class ControllerServiceAsyncStub:
    ProcessTestSuiteResults: grpc.aio.UnaryUnaryMultiCallable[
        kubekarma.grpcgen.collectors.v1.controller_pb2.ProcessTestSuiteResultsRequest,
        kubekarma.grpcgen.collectors.v1.controller_pb2.ProcessTestSuiteResultsResponse,
    ]
    """ProcessTestSuiteResults is called by the test runner to report the results of the execution"""

class ControllerServiceServicer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def ProcessTestSuiteResults(
        self,
        request: kubekarma.grpcgen.collectors.v1.controller_pb2.ProcessTestSuiteResultsRequest,
        context: _ServicerContext,
    ) -> typing.Union[kubekarma.grpcgen.collectors.v1.controller_pb2.ProcessTestSuiteResultsResponse, collections.abc.Awaitable[kubekarma.grpcgen.collectors.v1.controller_pb2.ProcessTestSuiteResultsResponse]]:
        """ProcessTestSuiteResults is called by the test runner to report the results of the execution"""

def add_ControllerServiceServicer_to_server(servicer: ControllerServiceServicer, server: typing.Union[grpc.Server, grpc.aio.Server]) -> None: ...
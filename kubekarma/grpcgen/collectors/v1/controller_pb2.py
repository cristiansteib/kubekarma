# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: kubekarma/grpcgen/collectors/v1/controller.proto
# Protobuf Python Version: 4.25.3
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n0kubekarma/grpcgen/collectors/v1/controller.proto\x12\x17kubekarma.collectors.v1\"\xbf\x02\n\x0eTestCaseResult\x12\x12\n\x04name\x18\x01 \x01(\tR\x04name\x12J\n\x06status\x18\x02 \x01(\x0e\x32\x32.kubekarma.collectors.v1.TestCaseResult.TestStatusR\x06status\x12-\n\x12\x65xecution_duration\x18\x03 \x01(\tR\x11\x65xecutionDuration\x12\x30\n\x14\x65xecution_start_time\x18\x04 \x01(\tR\x12\x65xecutionStartTime\x12#\n\rerror_message\x18\x05 \x01(\tR\x0c\x65rrorMessage\"G\n\nTestStatus\x12\t\n\x05\x45RROR\x10\x00\x12\r\n\tSUCCEEDED\x10\x01\x12\n\n\x06\x46\x41ILED\x10\x02\x12\x13\n\x0fNOT_IMPLEMENTED\x10\x03\"\xc7\x01\n\x1eProcessTestSuiteResultsRequest\x12\x12\n\x04name\x18\x01 \x01(\tR\x04name\x12&\n\x0fstarted_at_time\x18\x02 \x01(\tR\rstartedAtTime\x12S\n\x11test_case_results\x18\x03 \x03(\x0b\x32\'.kubekarma.collectors.v1.TestCaseResultR\x0ftestCaseResults\x12\x14\n\x05token\x18\x04 \x01(\tR\x05token\";\n\x1fProcessTestSuiteResultsResponse\x12\x18\n\x07message\x18\x01 \x01(\tR\x07message2\xa4\x01\n\x11\x43ontrollerService\x12\x8e\x01\n\x17ProcessTestSuiteResults\x12\x37.kubekarma.collectors.v1.ProcessTestSuiteResultsRequest\x1a\x38.kubekarma.collectors.v1.ProcessTestSuiteResultsResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'kubekarma.grpcgen.collectors.v1.controller_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_TESTCASERESULT']._serialized_start=78
  _globals['_TESTCASERESULT']._serialized_end=397
  _globals['_TESTCASERESULT_TESTSTATUS']._serialized_start=326
  _globals['_TESTCASERESULT_TESTSTATUS']._serialized_end=397
  _globals['_PROCESSTESTSUITERESULTSREQUEST']._serialized_start=400
  _globals['_PROCESSTESTSUITERESULTSREQUEST']._serialized_end=599
  _globals['_PROCESSTESTSUITERESULTSRESPONSE']._serialized_start=601
  _globals['_PROCESSTESTSUITERESULTSRESPONSE']._serialized_end=660
  _globals['_CONTROLLERSERVICE']._serialized_start=663
  _globals['_CONTROLLERSERVICE']._serialized_end=827
# @@protoc_insertion_point(module_scope)

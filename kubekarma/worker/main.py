import dataclasses
import datetime
import os
from typing import List

import urllib3
import yaml

from kubekarma.shared.pb2 import controller_pb2

from kubekarma.worker.networksuite.testsuite import NetworkTestSuite
from kubekarma.worker.sender import ControllerCommunication

import logging


# logger to stdout
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ExecutionTaskConfig:
    identifier: str
    controller_grpc_address: str
    test_suite_spec: dict
    test_suite_kind: str

    @classmethod
    def from_envs(cls) -> 'ExecutionTaskConfig':
        cls.validate_envs_are_set()
        return cls(
            identifier=os.getenv("WORKER_TASK_ID"),
            test_suite_spec=read_yaml(
                os.getenv("WORKER_TASK_EXECUTION_CONFIG")
            ),
            test_suite_kind=os.getenv("WORKER_TEST_SUITE_KIND"),
            controller_grpc_address=os.getenv("WORKER_CONTROLLER_OPERATOR_URL")
        )

    @classmethod
    def validate_envs_are_set(cls):
        """Validate that the required environment variables are set."""
        envs = [
            "WORKER_TASK_ID",
            "WORKER_TASK_EXECUTION_CONFIG",
            "WORKER_CONTROLLER_OPERATOR_URL",
            "WORKER_TEST_SUITE_KIND"
        ]
        for env in envs:
            if env not in os.environ:
                raise Exception(f"Environment variable {env} is not set")


def perform_task_execution(
    task: ExecutionTaskConfig
) -> List[controller_pb2.TestCaseResult]:
    test_suite = None
    if task.test_suite_kind == NetworkTestSuite.KIND:
        test_suite = NetworkTestSuite(task.test_suite_spec)
    else:
        raise Exception(
            f"Unsupported test suite kind: {task.test_suite_kind}"
        )
    return test_suite.run()


def read_yaml(stream: str) -> dict:
    return yaml.safe_load(stream)


timeout = urllib3.Timeout(connect=2.0, read=5.0)
http = urllib3.PoolManager(timeout=timeout)


if __name__ == "__main__":
    logger.info("Starting worker...")
    started_at_time = datetime.time().isoformat()
    task_config = ExecutionTaskConfig.from_envs()
    controller = ControllerCommunication(task_config.controller_grpc_address)
    results = perform_task_execution(task_config)
    # ControllerCommunication and is too tight to the proto,
    # it should be agnostic to the communication channel, and instead
    # use a DTO. But, to avoid the overhead of create classes and conversions
    # I will keep it like this for now.
    controller.send_results(
        controller_pb2.ProcessTestSuiteResultsRequest(
            started_at_time=started_at_time,
            token=task_config.identifier,
            test_case_results=results
        )
    )

import dataclasses
import datetime
import os

import yaml


from kubekarma.worker.abs.ikubekarmatestsuite import IKubekarmaTestSuite
from kubekarma.worker.networksuite.testsuite import NetworkKubekarmaTestSuite
from kubekarma.worker.sender import ControllerCommunication

import logging

from kubekarma.worker.testsuiteexecutor import TestSuiteExecutor

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


def get_kubekarma_test_suite_from_kind(
    kind: str,
    spec: dict
) -> IKubekarmaTestSuite:
    if kind == NetworkKubekarmaTestSuite.kind:
        return NetworkKubekarmaTestSuite(spec)
    else:
        raise Exception(
            f"Unsupported test suite kind: {kind}"
        )


def read_yaml(stream: str) -> dict:
    return yaml.safe_load(stream)


if __name__ == "__main__":
    logger.info("Starting worker...")
    started_at_time = datetime.datetime.now().isoformat()
    task_config = ExecutionTaskConfig.from_envs()
    controller = ControllerCommunication(task_config.controller_grpc_address)
    test_executor = TestSuiteExecutor(
        get_kubekarma_test_suite_from_kind(
            task_config.test_suite_kind,
            task_config.test_suite_spec
        ),
        token=task_config.identifier
    )
    controller.send_results(
        test_executor.execute()
    )

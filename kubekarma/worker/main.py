import os
from typing import List

import urllib3
import yaml

from kubekarma.dto.genericcrd import TestCaseResultItem
from kubekarma.dto.executiontask import ExecutionTaskConfig
from kubekarma import __version__ as package_version
from kubekarma.worker.nwtestsuite import NetworkTestSuite
from kubekarma.worker.sender import ControllerCommunication

import logging


# logger to stoud
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def perform_task_execution(
        task: ExecutionTaskConfig
) -> List[TestCaseResultItem]:
    if task.controller_version != package_version:
        raise Exception(
            "Controller version mismatch: "
            f"{task.controller_version} != {package_version}"
        )
    npts = NetworkTestSuite(config_spec=task.np_test_suite_spec)
    return npts.run()


def read_yaml(stream: str) -> dict:
    return yaml.safe_load(stream)


timeout = urllib3.Timeout(connect=2.0, read=5.0)
http = urllib3.PoolManager(timeout=timeout)


def validate_envs_are_set():
    envs = [
        "WORKER_TASK_ID",
        "WORKER_CONTROLLER_VERSION",
        "WORKER_TASK_EXECUTION_CONFIG",
        "NPTS_CONTROLLER_OPERATOR_URL",
    ]
    for env in envs:
        if env not in os.environ:
            raise Exception(f"Environment variable {env} is not set")


if __name__ == "__main__":
    print("Starting worker...")
    validate_envs_are_set()
    controller_url = os.getenv("NPTS_CONTROLLER_OPERATOR_URL")
    controller = ControllerCommunication(controller_url)
    succeed = controller.ping_controller()
    if not succeed:
        raise Exception(f"Controller is not available: {controller_url}")
    task_work_identifier = os.getenv("WORKER_TASK_ID")
    task_config = ExecutionTaskConfig(
        identifier=task_work_identifier,
        controller_version=os.getenv("WORKER_CONTROLLER_VERSION"),
        np_test_suite_spec=read_yaml(os.getenv("WORKER_TASK_EXECUTION_CONFIG")),
    )
    results = perform_task_execution(task_config)
    controller.send_results(task_config.identifier, results)
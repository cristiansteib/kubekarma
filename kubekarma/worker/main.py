import os
from typing import List

import urllib3
import yaml

from kubekarma.dto.executiontask import ExecutionTaskConfig, TestResults
from kubekarma import __version__ as package_version
from kubekarma.worker.nwtestsuite import NetworkPolicyTestSuite

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

def perform_task_execution(task: ExecutionTaskConfig) -> List[TestResults]:
    if task.controller_version != package_version:
        raise Exception(
            f"Controller version mismatch: {task.controller_version} != {package_version}"
        )
    npts = NetworkPolicyTestSuite(config_spec=task.np_test_suite_spec)
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
    logger.info("Ping controller <%s>...", controller_url)
    response = http.request(
        "GET",
        f"{controller_url}/healthz"
    )
    if response.status != 200:
        raise Exception(f"Controller is not ready: {response.status}")
    task_config = ExecutionTaskConfig(
        identifier=os.getenv("WORKER_TASK_ID"),
        controller_version=os.getenv("WORKER_CONTROLLER_VERSION"),
        np_test_suite_spec=read_yaml(os.getenv("WORKER_TASK_EXECUTION_CONFIG")),
    )
    results = perform_task_execution(task_config)
    payload = [result.to_dict() for result in results]
    response = http.request(
        "POST",
        f"{controller_url}/api/v1/execution-tasks/{task_config.identifier}",
    )
    if response.status != 200:
        raise Exception(f"Failed to post results: {response.status}")
    print("Worker finishasdef5dsfeds5dd.dsgfsadsfgfg")

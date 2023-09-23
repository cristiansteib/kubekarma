import os
import uuid
from pathlib import Path

import kubernetes
import yaml

from kubekarma.controlleroperator import TOOL_NAME
import logging

from kubekarma.controlleroperator.config import config

logger = logging.getLogger(__name__)


class _CronJobGenerator:
    @classmethod
    def populate(
        cls,
        job_template: dict,
        job_name: str,
        namespace: str,
        schedule: str,
        envs: list
    ) -> dict:
        job_template['spec']['schedule'] = schedule
        job_template['metadata']['name'] = job_name
        job_template['metadata']['namespace'] = namespace
        job_template['spec']['jobTemplate']['spec']['template']['spec'][
            'containers'][0]['env'] = envs
        return job_template


def handle_npts_creation(body: dict) -> dict:
    # random secure uid
    network_policy_test_suite_name = body['metadata']['name']
    job_name = TOOL_NAME + "-" + network_policy_test_suite_name
    logger.info("Creating job for task <%s>...", body['metadata']['name'])
    envs = [
        kubernetes.client.V1EnvVar(
            name='WORKER_TASK_ID',
            value=uuid.uuid4().hex
        ),
        kubernetes.client.V1EnvVar(
            name='WORKER_CONTROLLER_VERSION',
            value='0.0.1'
        ),
        kubernetes.client.V1EnvVar(
            name='WORKER_TASK_EXECUTION_CONFIG',
            value=yaml.dump(body['spec'])
        ),
        kubernetes.client.V1EnvVar(
            name='NPTS_CONTROLLER_OPERATOR_URL',
            value=config.controller_server_host
        ),
    ]
    path = Path(
        os.path.dirname(os.path.abspath(__file__))
    ) / "npts_job_template.yaml"
    namespace = body['metadata']['namespace']
    with open(path) as f:
        return _CronJobGenerator.populate(
            job_template=yaml.safe_load(f),
            schedule=body['spec']['schedule'],
            namespace=namespace,
            job_name=job_name,
            envs=envs
        )

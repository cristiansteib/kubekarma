import uuid
from typing import Optional

import kopf
from kubernetes import client
from kubernetes.client import (
    ApiClient,
    V1CronJob,
    V1EnvVar,
    BatchV1Api,
    V1ObjectMeta
)
import yaml

from kubekarma.controlleroperator import TOOL_NAME
from kubekarma.controlleroperator.config import config

import logging

logger = logging.getLogger(__name__)


class NetworkPolicyTestSuiteHandler:

    def __init__(self):
        self.__api_client: Optional[client.ApiClient] = None

    @property
    def _api_client(self) -> ApiClient:
        """Return the api client."""
        if not self.__api_client:
            self.__api_client = client.ApiClient()
        return self.__api_client

    def handle(self, spec, body, **kwargs):
        """A handler to receive a NetworkPolicyTestSuite creation event."""
        kopf.info(
            body,
            reason='Creation received by controller',
            message=f'Handling {body["kind"]}  <{body["spec"]["name"]}>'
        )
        namespace = body['metadata']['namespace']
        spec = body['spec']
        schedule = spec['schedule']
        cron_job = self.__generate_cronjob(
            npts_metadata_name=body['metadata']['name'] + "-npts" + uuid.uuid4().hex[:4],
            namespace=body['metadata']['namespace'],
            schedule=schedule,
            task_execution_config=body['spec']
        ).to_dict()
        kopf.adopt(cron_job, owner=body)
        BatchV1Api(
            api_client=self._api_client
        ).create_namespaced_cron_job(
            namespace=namespace,
            body=cron_job
        )
        # kubernetes_api.mutate_crd_satus(body, 'Running')
        kopf.info(
            body,
            reason='ready',
            message='detected creation'
        )

    @staticmethod
    def __generate_cronjob(
        npts_metadata_name,
        namespace,
        schedule,
        task_execution_config: dict
    ) -> V1CronJob:
        """Generate the job template to be used by the cronjob."""
        envs = [
            V1EnvVar(
                name='WORKER_TASK_ID',
                value=uuid.uuid4().hex
            ),
            V1EnvVar(
                name='WORKER_CONTROLLER_VERSION',
                value='0.0.1'
            ),
            V1EnvVar(
                name='WORKER_TASK_EXECUTION_CONFIG',
                value=yaml.dump(task_execution_config)
            ),
            V1EnvVar(
                name='NPTS_CONTROLLER_OPERATOR_URL',
                value=config.controller_server_host
            ),
        ]
        cron_job = V1CronJob()
        cron_job.metadata = V1ObjectMeta(
            name=TOOL_NAME + "-" + npts_metadata_name,
            namespace=namespace,
        )
        cron_job.spec = {
            "schedule": schedule,
            "jobTemplate": {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {
                                    "name": TOOL_NAME,
                                    "image": config.worker_image,
                                    "env": envs
                                }
                            ],
                            "restartPolicy": "Never"
                        }
                    }
                }
            }
        }
        return cron_job

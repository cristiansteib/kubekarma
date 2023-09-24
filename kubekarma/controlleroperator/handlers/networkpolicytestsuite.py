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

from controlleroperator import helpers
from kubekarma.controlleroperator import TOOL_NAME
from kubekarma.controlleroperator.config import config

import logging

logger = logging.getLogger(__name__)


class NetworkPolicyTestSuiteHandler:
    # We need a version for this handler in order to know if the operator
    # must change some of the CRD fields or execute some actions.
    # Note that this value is used in an annotation, so it must be compatible
    # with the annotation key format.
    HANDLER_VERSION = 'v1'

    API_PLURAL = 'networkpolicytestsuites'

    def __init__(self):
        self.__api_client: Optional[client.ApiClient] = None

    @property
    def _api_client(self) -> ApiClient:
        """Return the api client."""
        if not self.__api_client:
            self.__api_client = client.ApiClient()
        return self.__api_client

    def __patch_crd(self, namespace: str, metadata_name: str, patch: dict):
        """Patch the CRD with the given patch."""
        client.CustomObjectsApi(
            api_client=self._api_client
        ).patch_namespaced_custom_object(
            group="kubekarma.io",
            version="v1",
            namespace=namespace,
            plural="networkpolicytestsuites",
            name=metadata_name,
            body=patch
        )

    def handle(self, spec, body, **kwargs):
        """A handler to receive a NetworkPolicyTestSuite creation event."""
        # NOTE: kopf._cogs.clients.events.post_event has a hardcoded
        # values to post events with "kopf" as the source.
        kopf.info(
            body,
            reason='Creation received by controller',
            message=f'Handling {body["kind"]}  <{spec["name"]}>'
        )

        namespace = body['metadata']['namespace']
        metadata_name = body['metadata']['name']
        schedule = spec['schedule']

        cron_job_name = metadata_name + "-npts-" + uuid.uuid4().hex[:4]

        cron_job = self.__generate_cronjob(
            npts_metadata_name=cron_job_name,
            namespace=body['metadata']['namespace'],
            schedule=schedule,
            task_execution_config=body['spec'],
        ).to_dict()


        # Adopt the cronjob to the parent object to be able to delete it
        # in cascade.
        kopf.adopt(cron_job, owner=body)

        # Effectively create the cronjob in the cluster
        BatchV1Api(
            api_client=self._api_client
        ).create_namespaced_cron_job(
            namespace=namespace,
            body=cron_job
        )

        # The CRD it must change its status to "Running" in order to be
        # considered as created.
        self.__patch_crd(
            namespace=namespace,
            metadata_name=metadata_name,
            patch={
                "status": {
                    "phase": "Running"
                }
            }
        )
        # Trigger an event for the CRD related to the creation of the cronjob
        kopf.info(
            body,
            reason='Running',
            message=f'CronJob created successfully <{cron_job_name}>'
        )

        # Patch the created CRD with annotation pointing to the created cronjob
        # and the code version used by this handler.
        # This will allow for future version perform the required changes.
        annotations = {}
        annotations.update(
            helpers.generate_custom_annotation(
                "cronjob",
                cron_job_name
            ).to_kv()
        )
        annotations.update(
            self._get_version_handler_notation()
        )
        self.__patch_crd(
            namespace=namespace,
            metadata_name=metadata_name,
            patch={
                "metadata": {
                    "annotations": annotations
                }
            }
        )

    @classmethod
    def _get_version_handler_notation(cls) -> dict:
        """Return a notation of the current code handler version."""
        return helpers.generate_custom_annotation(
            "npts-handler-version",
            cls.HANDLER_VERSION
        ).to_kv()

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
        cron_job.metadata.annotations = (
            NetworkPolicyTestSuiteHandler._get_version_handler_notation()
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

import yaml
from kubernetes.client import V1CronJob, V1EnvVar, V1ObjectMeta

from kubekarma.controlleroperator.config import Config
from kubekarma.controlleroperator.kinds.crdinstancemanager import (
    CRDInstance
)


class CronJobHelper:

    @staticmethod
    def generate_cronjob(
        crd_instance: CRDInstance,
        schedule: str,
        task_execution_config: dict,
        config: Config,
        kind: str
    ) -> V1CronJob:
        """Generate the job template to be used by the cronjob."""

        cron_job = V1CronJob()
        cron_job.metadata = V1ObjectMeta(
            name=crd_instance.cron_job_name,
            namespace=crd_instance.namespace,
        )
        envs = [
            V1EnvVar(
                name='WORKER_TASK_ID',
                value=crd_instance.worker_task_id
            ),

            V1EnvVar(
                name='WORKER_TASK_EXECUTION_CONFIG',
                value=yaml.dump(task_execution_config)
            ),
            V1EnvVar(
                name='WORKER_CONTROLLER_OPERATOR_URL',
                value=config.controller_server_host
            ),
            V1EnvVar(
                name='WORKER_TEST_SUITE_KIND',
                value=kind
            ),
        ]

        cron_job.spec = {
            "schedule": schedule,
            "concurrencyPolicy": "Forbid",
            "successfulJobsHistoryLimit": 2,
            "failedJobsHistoryLimit": 4,

            "jobTemplate": {
                "spec": {
                    "backoffLimit": 0,
                    "ttlSecondsAfterFinished": 60 * 60 * 5,
                    "template": {
                        "spec": {
                            "restartPolicy": "Never",
                            "containers": [
                                {
                                    "name": "kubekarma-worker",
                                    "image": config.worker_image,
                                    "env": envs
                                }
                            ],
                        }
                    }
                }
            }
        }
        return cron_job

import unittest

from kubernetes.client import V1CronJob

from kubekarma.controlleroperator.config import Config
from kubekarma.controlleroperator.core.crdinstancemanager import CRD
from kubekarma.controlleroperator.core.cronjob import CronJobHelper


class CronJobHelperTest(unittest.TestCase):

    def test_create_cronjob(self):
        cron = CronJobHelper.generate_cronjob(
            crd_instance=CRD(
                namespace="default",
                plural="NetworkKubarmaTestSuite",
                metadata_name="test-suite-1",
                cron_job_name="test-suite-1-npts-1234",
                worker_task_id="1234"
            ),
            schedule="* * * * *",
            task_execution_config={
                "name": "test-suite-1",
                "networkValidations": [
                    {
                        "testExactDestination": {
                            "destinationIp": "1.1.1.1",
                            "port": 80,
                            "expectSuccess": False
                        }
                    }
                ]
            },
            kind="NetworkKubarmaTestSuite",
            config=Config(
                controller_server_host="http://localhost:5000",
                worker_image="kubekarma/worker:latest",
                log_level=1
            )
        )
        self.assertIsInstance(cron, V1CronJob)
        self.assertIsInstance(cron.to_dict(), dict)

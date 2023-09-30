import dataclasses
import uuid
from datetime import datetime
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

from kubekarma.shared.genericcrd import CRDTestExecutionStatus, \
    CRDTestPhase, TestCaseStatus
from kubekarma.shared.crd.networktestsuite import (
    NetworkTestSuiteCRD
)
from kubekarma.controlleroperator.abc.resultspublisher import (
    IResultsPublisher,
    IResultsSubscriber
)
from kubekarma.controlleroperator import helpers
from kubekarma.controlleroperator import TOOL_NAME
from kubekarma.controlleroperator.config import config

import logging

from kubekarma.shared.pb2 import controller_pb2

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class CtxCRDInstance:
    """A class to keep a track of the CRD created."""
    namespace: str
    metadata_name: str
    cron_job_name: str
    worker_task_id: str


class CRDInstanceManager:

    def __init__(self, api_client: ApiClient, ctx: CtxCRDInstance):
        self.api_client = api_client
        self.ctx = ctx

    def patch_crd(self, patch: dict):
        """Patch the CRD with the given patch."""
        client.CustomObjectsApi(
            api_client=self.api_client
        ).patch_namespaced_custom_object(
            group="kubekarma.io",
            version="v1",
            namespace=self.ctx.namespace,
            plural="networktestsuites",
            name=self.ctx.metadata_name,
            body=patch
        )

    def patch_with_handler_code_version_notation(self, handler_code_version):
        """Patch the CRD with the given patch."""
        annotations = {}
        annotations.update(
            helpers.generate_custom_annotation(
                "npts-handler-version",
                handler_code_version
            ).to_kv()
        )

        self.patch_crd(
            patch={
                "metadata": {
                    "annotations": annotations
                }
            }
        )

    def patch_with_cronjob_notation(self, ctx):
        annotations = {}
        annotations.update(
            helpers.generate_custom_annotation(
                "cronjob",
                ctx.cron_job_name
            ).to_kv()
        )
        self.patch_crd(
            patch={
                "metadata": {
                    "annotations": annotations
                }
            }
        )


class ResultsSubscriber(IResultsSubscriber):

    def __init__(self, crd_manager: CRDInstanceManager):
        self.crd_manager = crd_manager

    @staticmethod
    def get_status(status: controller_pb2.TestStatus) -> TestCaseStatus:
        """Return the test case status defined by the CRD."""
        if status == controller_pb2.TestStatus.SUCCEEDED:
            return TestCaseStatus.Succeeded
        elif status == controller_pb2.TestStatus.FAILED:
            return TestCaseStatus.Failed
        elif status == controller_pb2.TestStatus.NOTIMPLEMENTED:
            return TestCaseStatus.NotImplemented
        elif status == controller_pb2.TestStatus.ERROR:
            return TestCaseStatus.Error
        else:
            raise Exception(f"Unknown status: {status}")

    def receive_results(
        self,
        results: controller_pb2.ProcessTestSuiteResultsRequest
    ):
        """Receive the results of some the execution task.

        This method is called by the publisher when the results of an
        execution task are available. The results should be interpreted
        and used to set  the status of the CRD.
        """
        # prepare the patch to be applied to the CRD to report the results
        test_cases = []
        # The whole test execution status
        test_execution_status = CRDTestExecutionStatus.Succeeding
        for result in results.test_case_results:
            test_status = self.get_status(result.status)
            test_case_status = {
                    # The unique name of the test case, we can consider this
                    # as the ID of the test case.
                    "name": result.name,
                    # The status of the test case.
                    "status": test_status.value,
                    # The time it took to execute the test case.
                    "executionTime": result.execution_duration,
                }

            # Check if the whole test suite should be marked as failing
            test_execution_status = (
                CRDTestExecutionStatus.Failing
                if test_status in (TestCaseStatus.Failed, TestCaseStatus.Error)
                else test_execution_status
            )
            if test_status == TestCaseStatus.Error:
                test_case_status["error"] = result.error_message
            test_cases.append(test_case_status)

        current_time = datetime.utcnow()
        current_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        # TODO: track last time status changed
        self.crd_manager.patch_crd(
            patch={
                "status": {
                    "lastExecutionTime": current_time_str,
                    "lastExecutionErrorTime": current_time_str if test_execution_status == CRDTestExecutionStatus.Failing else "",
                    "lastSucceededTime": current_time_str if test_execution_status == CRDTestExecutionStatus.Succeeding else "",
                    "testExecutionStatus":  test_execution_status.value,
                    "testCases": test_cases
                }
            }
        )

    def __hash__(self):
        return hash(id(self))


class NetworkTestSuiteHandler:
    """This class is the responsible to handle the lifecycle of the CRD.

    On creation:
        - Create a cronjob to execute the tests defined by the user.
        - Create a subscriber to listen for the results of the execution task.
    """
    # We need a version for this handler in order to know if the operator
    # must change some of the CRD fields or execute some actions.
    # Note that this value is used in an annotation, so it must be compatible
    # with the annotation key format.
    HANDLER_VERSION = 'v1'

    API_PLURAL = 'networktestsuites'

    def __init__(self, publisher: IResultsPublisher):
        self.__api_client: Optional[client.ApiClient] = None
        self.publisher = publisher
        logger.info("publisher: %s", id(publisher))
        print("publisher id:", id(publisher))

    @property
    def _api_client(self) -> ApiClient:
        """Return the api client."""
        if not self.__api_client:
            self.__api_client = client.ApiClient()
        return self.__api_client

    def __patch_crd(self, ctx: CtxCRDInstance, patch: dict):
        """Patch the CRD with the given patch."""
        client.CustomObjectsApi(
            api_client=self._api_client
        ).patch_namespaced_custom_object(
            group="kubekarma.io",
            version="v1",
            namespace=ctx.namespace,
            plural="networktestsuites",
            name=ctx.metadata_name,
            body=patch
        )

    def set_crd_phase(self, ctx: CtxCRDInstance, phase: CRDTestPhase):
        """Set the phase of the CRD."""
        patch = {
            "status": {
                "phase": phase.value,
             }
        }
        if phase in (CRDTestPhase.Created, CRDTestPhase.Pending, CRDTestPhase.Suspended): # noqa
            # Generic CRD status
            patch["status"]["testExecutionStatus"] = CRDTestExecutionStatus.Pending.value # noqa
        self.__patch_crd(
            ctx=ctx,
            patch=patch
        )

    def handle(self, spec, body, **kwargs):
        """A handler to receive a NetworkTestSuite creation event."""
        # NOTE: kopf._cogs.clients.events.post_event has a hardcoded
        # values to post events with "kopf" as the source.
        kopf.info(
            body,
            reason='Creation received by controller',
            message=f'Handling {body["kind"]}  <{spec["name"]}>'
        )

        worker_task_id = uuid.uuid4().hex
        ctx = CtxCRDInstance(
            namespace=body['metadata']['namespace'],
            metadata_name=body['metadata']['name'],
            cron_job_name=body['metadata']['name'] + "-npts-" + worker_task_id[:4], # noqa
            worker_task_id=uuid.uuid4().hex
        )

        crd_manager = CRDInstanceManager(
            api_client=self._api_client,
            ctx=ctx
        )

        logger.debug("Validating CRD [%s:%s]", ctx.namespace, ctx.metadata_name)
        errors = NetworkTestSuiteCRD().validate_spec(
            spec=spec
        )
        if errors:
            self.set_crd_phase(ctx, CRDTestPhase.Failed)
            raise kopf.PermanentError(
                f"Invalid spec: {yaml.dump(errors)}" # noqa
            )
        self.set_crd_phase(ctx, CRDTestPhase.Created)
        cron_job = self.__generate_cronjob(
            crd_instance=ctx,
            schedule=spec['schedule'],
            task_execution_config=body['spec'],
        ).to_dict()

        # Adopt the cronjob to the parent object to be able to delete it
        # in cascade.
        kopf.adopt(cron_job, owner=body)

        # Effectively create the cronjob in the cluster
        BatchV1Api(
            api_client=self._api_client
        ).create_namespaced_cron_job(
            namespace=ctx.namespace,
            body=cron_job
        )

        # Listen for the results of the execution task that run in a pod
        # controlled by a CronJob running on a specific namespace.
        self.publisher.add_results_listener(
            execution_id=ctx.worker_task_id,
            subscriber=ResultsSubscriber(crd_manager)
        )

        # Trigger an event for the CRD related to the creation of the cronjob
        kopf.info(
            body,
            reason='Running',
            message=f'CronJob created successfully <{ctx.cron_job_name}>'
        )

        # Patch the created CRD with annotation pointing to the created cronjob
        # and the code version used by this handler.
        # This will allow for future version perform the required changes.
        crd_manager.patch_with_cronjob_notation(ctx)
        crd_manager.patch_with_handler_code_version_notation(
            handler_code_version=self.HANDLER_VERSION
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
        crd_instance: CtxCRDInstance,
        schedule,
        task_execution_config: dict,
    ) -> V1CronJob:
        """Generate the job template to be used by the cronjob."""
        envs = [
            V1EnvVar(
                name='WORKER_TASK_ID',
                value=crd_instance.worker_task_id
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
            name=crd_instance.cron_job_name,
            namespace=crd_instance.namespace,
        )
        cron_job.metadata.annotations = (
            NetworkTestSuiteHandler._get_version_handler_notation()
        )
        cron_job.spec = {
            "schedule": schedule,
            "jobTemplate": {
                "spec": {
                    "template": {
                        "spec": {
                            "successfulJobsHistoryLimit": 5,
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

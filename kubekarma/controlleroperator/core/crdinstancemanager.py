import contextvars
import dataclasses

import kopf
from kopf import Body
from kopf._cogs.structs import bodies
from kubernetes import client
from kubernetes.client import ApiClient, V1CronJob

from kubekarma.controlleroperator.config import config
from kubekarma.controlleroperator.core.testsuite.types import \
    TestSuiteStatusType
from kubekarma.shared.crd.genericcrd import CRDTestExecutionStatus, \
    CRDTestPhase
import logging

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class CRD:
    """A class to keep a track of some CRD Test Suite created."""
    namespace: str
    metadata_name: str
    cron_job_name: str
    worker_task_id: str
    plural: str

    @staticmethod
    def __get_key(key: str) -> str:
        """Generate a key for kubekarma.io."""
        return f"{config.API_GROUP}/{key}"

    def generate_annotations(self) -> dict:
        annotations = {
            self.__get_key("cronjob"): self.cron_job_name,
            self.__get_key("worker-task-id"): self.worker_task_id
        }
        return annotations

    def validate(self):
        """Validate if all properties are defined."""
        if not self.namespace:
            raise ValueError("namespace is required")
        if not self.metadata_name:
            raise ValueError("metadata_name is required")
        if not self.cron_job_name:
            raise ValueError("worker_task_id is required")
        if not self.worker_task_id:
            raise ValueError("worker_task_id is required")
        if not self.plural:
            raise ValueError("plural is required")

    @classmethod
    def from_body(cls, body: Body, plural: str) -> "CRD":
        """Create a CRD instance from a body."""
        return cls(
            namespace=body["metadata"]["namespace"],
            metadata_name=body["metadata"]["name"],
            cron_job_name=body["metadata"]["annotations"][
                cls.__get_key("cronjob")
            ],
            worker_task_id=body["metadata"]["annotations"][
                cls.__get_key("worker-task-id")
            ],
            plural=plural,
        )


class CRDInstanceManager:

    def __init__(
        self,
        api_client: ApiClient,
        crd_ctx: CRD,
        body: bodies.Body,
        contextvars_copy: contextvars.Context
    ):
        """Initialize the CRDInstanceManager.

        Intention: Provide a single way to manipulate the CRD instance status,
            or trigger events.

        Args:
            api_client (ApiClient): The api client to use to interact with
                the kubernetes API.
            crd_ctx (CRD): The data of the CRD instance.
            body (bodies.Body): The body of the CRD instance.
            contextvars_copy (contextvars.Context): Used for a
                Manual Context Management.
                This Context is required due to how kopf works, it relies on
                the ContextVar to manage independent settings for each handler.
        """
        self.api_client = api_client
        self.crd_data = crd_ctx
        self._contextvars_copy = contextvars_copy
        # cache the data required by:
        #   kopf._cogs.structs.bodies.build_object_reference
        self.body_cache = bodies.Body({
            "apiVersion": body["apiVersion"],
            "kind": body["kind"],
            "metadata": {
                "name": body["metadata"]["name"],
                "namespace": body["metadata"]["namespace"],
                "uid": body["metadata"]["uid"],
            }
        })

    def info_event(self, reason: str, message: str):
        # NOTE: kopf._cogs.clients.events.post_event has a hardcoded
        # values to post events with "kopf" as the source.
        self._contextvars_copy.run(
            kopf.info,
            self.body_cache,
            reason=reason,
            message=message,
        )

    def error_event(self, reason: str, message: str):
        # NOTE: kopf._cogs.clients.events.post_event has a hardcoded
        # values to post events with "kopf" as the source.
        self._contextvars_copy.run(
            kopf.event,
            self.body_cache,
            reason=reason,
            message=message,
            type="Error"
        )

    def _patch_crd(self, patch: dict):
        """Patch the CRD with the given patch."""
        client.CustomObjectsApi(
            api_client=self.api_client
        ).patch_namespaced_custom_object(
            group=config.API_GROUP,
            version=config.API_VERSION,
            namespace=self.crd_data.namespace,
            plural=self.crd_data.plural,
            name=self.crd_data.metadata_name,
            body=patch
        )

    def set_test_suite_result_status(self, status: TestSuiteStatusType):
        """Set the status of the test execution.

        This method set the .status of the CRD with the information related
        to the test execution.
        """
        patch = {
            "status": status
        }
        self._patch_crd(patch=patch)

    def set_phase_to_active(self):
        """Set the status of the CRD to Active."""
        return self._set_crd_phase(CRDTestPhase.Active)

    def set_phase_to_pending(self):
        """Set the status of the CRD to Pending."""
        return self._set_crd_phase(CRDTestPhase.Pending)

    def set_phase_to_suspended(self):
        """Set the status of the CRD to Suspended."""
        return self._set_crd_phase(CRDTestPhase.Suspended)

    def set_phase_to_failed(self):
        """Set the status of the CRD to Failed."""
        return self._set_crd_phase(CRDTestPhase.Failed)

    def _set_crd_phase(self, phase: CRDTestPhase):
        """Set the phase of the CRD.

        The CRD phase represents the status of crd itself, not the status
        of the test execution.
        """
        assert isinstance(phase, CRDTestPhase)
        """Set the phase of the CRD."""
        patch = {
            "status": {
                "phase": phase.value,
            }
        }
        correct_status = (
            CRDTestPhase.Active,
            CRDTestPhase.Pending,
            CRDTestPhase.Suspended
        )
        if phase in correct_status:
            # Generic CRD status
            patch["status"]["testExecutionStatus"] = (
                CRDTestExecutionStatus.Pending.value
            )
        self._patch_crd(patch=patch)

    def save(self):
        """Save the state of the CRD ctx instance."""
        # validate all properties are defined
        self.crd_data.validate()
        self._patch_crd(
            patch={
                "metadata": {
                    "annotations": self.crd_data.generate_annotations()
                }
            }
        )

    def set_cronjob_suspend(self, suspend: bool):
        """Suspend the cronjob."""
        job_name = self.crd_data.cron_job_name
        logger.info(f"Suspending cronjob {job_name}")
        client.BatchV1Api(
            api_client=self.api_client
        ).patch_namespaced_cron_job(
            name=job_name,
            namespace=self.crd_data.namespace,
            body={
                "spec": {
                    "suspend": suspend
                }
            }
        )

    def create_cron_job(
        self,
        cron_job: V1CronJob
    ) -> V1CronJob:
        return client.BatchV1Api(
            api_client=self.api_client
        ).create_namespaced_cron_job(
            namespace=self.crd_data.namespace,
            body=cron_job
        )

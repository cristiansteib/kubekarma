import dataclasses

import kopf
from kopf._cogs.structs import bodies
from kubernetes import client
from kubernetes.client import ApiClient

from kubekarma.controlleroperator import helpers
from kubekarma.shared.crd.genericcrd import CRDTestExecutionStatus, \
    CRDTestPhase


@dataclasses.dataclass
class CtxCRDInstance:
    """A class to keep a track of some CRD Test Suite created."""
    namespace: str
    metadata_name: str
    cron_job_name: str
    worker_task_id: str
    plural: str


class CRDInstanceManager:

    def __init__(
        self,
        api_client: ApiClient,
        ctx: CtxCRDInstance,
        body: bodies.Body
    ):
        self.api_client = api_client
        self.ctx = ctx
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
        kopf.info(
            self.body_cache,
            reason=reason,
            message=message,
        )

    def error_event(self, reason: str, message: str):
        kopf.exception(
            self.body_cache,
            reason=reason,
            message=message,
        )

    def patch_crd(self, patch: dict):
        """Patch the CRD with the given patch."""
        client.CustomObjectsApi(
            api_client=self.api_client
        ).patch_namespaced_custom_object(
            group="kubekarma.io",
            version="v1",
            namespace=self.ctx.namespace,
            plural=self.ctx.plural,
            name=self.ctx.metadata_name,
            body=patch
        )

    def set_crd_phase(self, phase: CRDTestPhase):
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
        self.patch_crd(patch=patch)

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

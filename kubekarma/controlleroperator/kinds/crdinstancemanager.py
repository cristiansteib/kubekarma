import dataclasses

from kubernetes import client
from kubernetes.client import ApiClient

from kubekarma.controlleroperator import helpers


@dataclasses.dataclass
class CtxCRDInstance:
    """A class to keep a track of some CRD Test Suite created."""
    namespace: str
    metadata_name: str
    cron_job_name: str
    worker_task_id: str
    plural: str


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
            plural=self.ctx.plural,
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

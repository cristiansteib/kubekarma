import uuid
from typing import Optional

import kopf
from kubernetes import client
from kubernetes.client import (
    ApiClient,
    BatchV1Api,
)
import yaml

from kubekarma.controlleroperator.kinds.networktestsuite import API_PLURAL
from kubekarma.controlleroperator.kinds.networktestsuite.testsubscriber import \
    ResultsSubscriber
from kubekarma.controlleroperator.kinds.networktestsuite.cronjob import \
    NetworkTestSuiteWorkerJob
from kubekarma.controlleroperator.kinds.crdinstancemanager import (
    CRDInstanceManager,
    CtxCRDInstance
)
from kubekarma.shared.crd.genericcrd import CRDTestExecutionStatus, \
    CRDTestPhase
from kubekarma.shared.crd.networktestsuite import (
    NetworkTestSuiteCRD
)
from kubekarma.controlleroperator.abc.resultspublisher import (
    IResultsPublisher
)
from kubekarma.controlleroperator.config import config

import logging

logger = logging.getLogger(__name__)


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

    def __init__(self, publisher: IResultsPublisher):
        self.__api_client: Optional[client.ApiClient] = None
        self.publisher = publisher
        logger.info("publisher: %s", id(publisher))

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
            plural=API_PLURAL,
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

    def handle_create(self, spec, body, **kwargs):
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
            worker_task_id=uuid.uuid4().hex,
            plural=API_PLURAL
        )

        crd_manager = CRDInstanceManager(
            api_client=self._api_client,
            ctx=ctx
        )

        logger.debug(
            "Validating CRD [%s:%s]",
            ctx.namespace,
            ctx.metadata_name
        )
        errors = NetworkTestSuiteCRD().validate_spec(
            spec=spec
        )
        if errors:
            self.set_crd_phase(ctx, CRDTestPhase.Failed)
            raise kopf.PermanentError(
                f"Invalid spec: {yaml.dump(errors)}" # noqa
            )
        self.set_crd_phase(ctx, CRDTestPhase.Created)

        cron_job = NetworkTestSuiteWorkerJob.generate_cronjob(
            crd_instance=ctx,
            schedule=spec['schedule'],
            task_execution_config=body['spec'],
            config=config
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

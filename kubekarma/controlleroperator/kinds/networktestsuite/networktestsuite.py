import contextvars
import uuid
from typing import Optional

import kopf
from kubernetes import client
from kubernetes.client import (
    ApiClient,
    BatchV1Api,
)
import yaml

from kubekarma.controlleroperator.kinds import KIND
from kubekarma.controlleroperator.kinds.networktestsuite import API_PLURAL
from kubekarma.controlleroperator.kinds.networktestsuite.resultssubscriber import \
    ResultsSubscriber
from kubekarma.controlleroperator.kinds.cronjob import \
    CronJobHelper
from kubekarma.controlleroperator.kinds.crdinstancemanager import (
    CRDInstanceManager,
    CRDInstance
)
from kubekarma.shared.crd.genericcrd import CRDTestPhase
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

    @property
    def _api_client(self) -> ApiClient:
        """Return the api client."""
        if not self.__api_client:
            self.__api_client = client.ApiClient()
        return self.__api_client

    @staticmethod
    def assert_is_correct_kind(current_kind: str):
        """Assert that the current kind is the expected one."""
        if current_kind != KIND:
            raise kopf.PermanentError(
                f"Invalid kind: {current_kind}. Expected {KIND}"
            )

    def handle_create(self, spec, body, **kwargs):
        """A handler to receive a NetworkTestSuite creation event."""
        # I need to copy the context to avoid an error on the kopf framework
        # related to the context management of the handlers, because
        # it uses the contextvars to store the settings of each handler.
        context_copy: contextvars.Context = contextvars.copy_context()
        self.assert_is_correct_kind(body['kind'])
        kopf.info(
            body,
            reason='CreationReceived',
            message=f'Handling {body["kind"]}  <{spec["name"]}>'
        )

        worker_task_id = uuid.uuid4().hex
        crd_data = CRDInstance(
            namespace=body['metadata']['namespace'],
            metadata_name=body['metadata']['name'],
            cron_job_name=body['metadata']['name'] + "-npts-" + worker_task_id[:4], # noqa
            worker_task_id=uuid.uuid4().hex,
            plural=API_PLURAL
        )

        crd_manager = CRDInstanceManager(
            api_client=self._api_client,
            crd_data=crd_data,
            body=body,
            contextvars_copy=context_copy
        )

        errors = NetworkTestSuiteCRD().validate_spec(
            spec=spec
        )
        if errors:
            crd_manager.set_crd_phase(CRDTestPhase.Failed)
            raise kopf.PermanentError(
                f"Invalid spec: {yaml.dump(errors)}" # noqa
            )
        crd_manager.set_crd_phase(CRDTestPhase.Active)
        cron_job = CronJobHelper.generate_cronjob(
            crd_instance=crd_data,
            schedule=spec['schedule'],
            task_execution_config=body['spec'],
            config=config,
            kind=KIND
        ).to_dict()

        # Adopt the cronjob to the parent object to be able to delete it
        # in cascade.
        kopf.adopt(cron_job, owner=body)

        # Effectively create the cronjob in the cluster
        BatchV1Api(
            api_client=self._api_client
        ).create_namespaced_cron_job(
            namespace=crd_data.namespace,
            body=cron_job
        )

        # Listen for the results of the execution task that run in a pod
        # controlled by a CronJob running on a specific namespace.
        self.publisher.add_results_listener(
            execution_id=crd_data.worker_task_id,
            subscriber=ResultsSubscriber(crd_manager)
        )

        # Trigger an event for the CRD related to the creation of the cronjob
        crd_manager.info_event(
            reason='Running',
            message=f'CronJob created successfully <{crd_data.cron_job_name}>'
        )
        # Patch the created CRD with annotation pointing to the created cronjob
        # and the code version used by this handler.
        # This will allow for future version perform the required changes.
        crd_manager.patch_with_cronjob_notation(crd_data)

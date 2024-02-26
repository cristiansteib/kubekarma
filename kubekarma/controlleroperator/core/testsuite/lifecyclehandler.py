import contextvars

import kopf
from kopf import Body, Spec

from kubekarma.controlleroperator.config import config
from kubekarma.controlleroperator.core.abc.testsuitekind import ITestSuiteKind
from kubekarma.controlleroperator.core.crdinstancemanager import CRD, \
    CRDInstanceManager

import logging

from kubekarma.controlleroperator.core.testsuite.controllercrdvalidator import \
    ControllerCRDValidator
from kubekarma.shared.loghelper import PrefixFilter

logger = logging.getLogger(__name__)

logger.addFilter(PrefixFilter("ControllerCRDLifecycleHandler: "))


class ControllerCRDLifecycleHandler:

    def __init__(
        self,
        test_suite_kind: ITestSuiteKind,
    ):
        """Initialize the handler."""

        self.kind = test_suite_kind.kind
        self.api_plural = test_suite_kind.api_plural
        self.controller_crd_validator = ControllerCRDValidator(
            validator=test_suite_kind.get_crd_validator()
        )
        self.test_suite_kind = test_suite_kind
        self.__crds_managers: dict[str, CRDInstanceManager] = {}

    def get_crd_manager(
        self,
        body: Body,
        crd: CRD,
    ):
        # I need to copy the context to avoid an error on the kopf framework
        # related to the context management of the handlers, because
        # it uses the contextvars to store the settings of each handler.
        context_copy: contextvars.Context = contextvars.copy_context()
        return CRDInstanceManager(
            api_client=self.test_suite_kind.api_client,
            crd_ctx=crd,
            body=body,
            contextvars_copy=context_copy
        )

    def handle_create(self, spec: Spec, body: Body, **kwargs):
        """Handle the creation of the CRD instance."""
        logger.info("Handling the creation of a CRD instance")
        self._assert_is_expected_kind(body)

        crd = self.test_suite_kind.get_crd_for_creation(
            namespace=body['metadata']['namespace'],
            metadata_name=body['metadata']['name'],
            api_plural=self.api_plural
        )
        crd_manager = self.get_crd_manager(
            body=body,
            crd=crd
        )
        self.__crds_managers[crd.metadata_name] = crd_manager
        if errors := self.controller_crd_validator.validate(spec):
            logger.error(
                "Invalid spec for %s/%s of kind %s: %s",

                crd.namespace,
                crd.metadata_name,
                self.kind,
                errors
            )
            crd_manager.set_phase_to_failed()
            crd_manager.error_event(
                reason="InvalidSpec",
                message=f"Invalid spec: {' '.join(errors)}"
            )
            return

        cron_job = self.test_suite_kind.generate_cron_job(
            kind=self.kind,
            crd=crd,
            schedule=spec['schedule'],
            task_execution_config=dict(spec),
            the_config=config
        )

        # Adopt the CronJob to set the owner reference in order to delete
        # the CronJob in cascade.
        kopf.adopt(cron_job, owner=body)  # type: ignore

        # Call the api to create the cronjob
        logger.info(
            "Creating cron job for %s/%s of kind %s",
            crd.namespace,
            crd.metadata_name,
            self.kind
        )
        crd_manager.create_cron_job(cron_job)

        crd_manager.info_event(
            reason="CronJobCreated",
            message=f"CronJob created: {cron_job.metadata.name}"
        )

        self.test_suite_kind.initialize_results_listeners(
            crd,
            dict(spec),
            crd_manager
        )

        # Store the information of the CRD instance
        crd_manager.save()

        # Set the phase of the CRD to Active
        crd_manager.set_phase_to_active()

    def handle_delete(self, spec, body, **kwargs):
        """Handle the deletion of the CRD instance.

        All Kubernetes objects related should be deleted, also the
        instance classes should be deleted.
        """
        self._assert_is_expected_kind(body)
        crd_manager = self.__crds_managers[body['metadata']['name']]
        crd = crd_manager.crd_data

        logger.info(
            "Removing all controller operations for %s/%s of kind %s",
            crd.namespace,
            crd.metadata_name,
            self.kind
        )

        self.test_suite_kind.remove_all_listeners(crd.worker_task_id)
        self.__crds_managers.pop(crd.metadata_name)

    def handle_update(self, spec, body, **kwargs):
        self._assert_is_expected_kind(body)

    def handle_resume_controller_restart(self, spec, body, **kwargs):
        """Resume the controller operations for on controller restarts.

        At this point the CronJob is already created, so the controller
        needs to be resumed using the information coming from the CRD.
        """
        self._assert_is_expected_kind(body)
        crd = CRD.from_body(body, self.api_plural)
        if crd.metadata_name in self.__crds_managers:
            logger.error("FUCK! CRD instance already exists: %s", crd.metadata_name)
            return

        logger.info(
            "Resuming controller operation after controller restart "
            "for %s/%s of kind %s",
            crd.namespace,
            crd.metadata_name,
            self.kind
        )
        # Generate the CRD manager as it was created by the handle_create
        crd_manager = self.get_crd_manager(
            body=body,
            crd=crd
        )
        self.__crds_managers[crd.metadata_name] = crd_manager

        # At this point the controller relies on the information stored
        # to resume the operations (listeners), also trust the CronJob
        # is already created and running.
        self.test_suite_kind.initialize_results_listeners(
            crd,
            dict(spec),
            crd_manager
        )

    def handle_suspend(self, spec, body, **kwargs):
        """Pause the controller operations for the CRD."""
        self._assert_is_expected_kind(body)
        crd_manager = self.__crds_managers[body['metadata']['name']]
        crd = crd_manager.crd_data
        suspend = spec['suspend']
        action = "Suspending" if suspend else "Resuming after suspension"
        logger.info(
            "%s controller operations for %s/%s of kind %s",
            action,
            crd.namespace,
            crd.metadata_name,
            self.kind
        )

        if suspend:
            crd_manager.set_cronjob_suspend(True)
            self.test_suite_kind.suspend_operations(crd_manager)
            crd_manager.set_phase_to_suspended()
            crd_manager.info_event(
                reason="TestSuiteSuspended",
                message="Test suite suspended"
            )
        else:
            crd_manager.set_cronjob_suspend(False)
            self.test_suite_kind.resume_operations(crd_manager, dict(spec))
            crd_manager.set_phase_to_active()
            crd_manager.info_event(
                reason="TestSuiteResumed",
                message="Test suite resumed "
            )

    def _assert_is_expected_kind(self, body: Body):
        """Validate if it is handling the correct kind.

        This method is intended to be used only for debugging purposes.
        """
        assert body["kind"] == self.kind, (
            f"Invalid kind: {body['kind']} expected {self.kind}"
        )

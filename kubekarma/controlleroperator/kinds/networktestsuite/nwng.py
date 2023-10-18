from kubekarma.controlleroperator.abc.resultspublisher import \
    IResultsSubscriber
from kubekarma.controlleroperator.kinds.crdinstancemanager import \
    CRDInstanceManager
from kubekarma.controlleroperator.kinds.networktestsuite import API_PLURAL, \
    KIND
from kubekarma.controlleroperator.kinds.networktestsuite.resultssubscriber import \
    ResultsSubscriber
from kubekarma.controlleroperator.kinds.testsuitekind import TestSuiteKindBase
from kubekarma.shared.crd.networktestsuite import NetworkTestSuiteCRD


class NetworkTestSuite(TestSuiteKindBase):

    kind = KIND
    api_plural = API_PLURAL
    crd_validator = NetworkTestSuiteCRD

    def get_results_subscriber(
        self,
        spec,
        crd_manager: CRDInstanceManager
    ) -> IResultsSubscriber:
        return ResultsSubscriber(
            schedule=spec['schedule'],
            crd_manager=crd_manager,
            controller_engine=self.controller_engine
        )

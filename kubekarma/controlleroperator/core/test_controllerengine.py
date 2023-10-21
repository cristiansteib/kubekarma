import unittest
from time import sleep, time

from kubekarma.controlleroperator.core.controllerengine import \
    ControllerEngine


def hello():
    print("Hello world")


class ControllerEngineTest(unittest.TestCase):

    def test_scheduler(self):
        controller_engine = ControllerEngine()
        t = controller_engine.start()

        controller_engine.scheduler.enterabs(
            time() + 25,
            1,
            hello
        )
        controller_engine.stop()
        t.join()
        sleep(1)

class AssertionFailure(Exception):

    def __init__(
        self,
        assertion,
        message
    ):
        self.assertion = assertion
        self.message = message

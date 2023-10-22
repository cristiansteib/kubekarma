import logging


class PrefixFilter(logging.Filter):

    def __init__(self, prefix):
        super().__init__()
        self.prefix = prefix

    def filter(self, record):
        record.msg = self.prefix + record.msg
        return True

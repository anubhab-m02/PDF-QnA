import logging
from io import StringIO

class StringIOHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.stream = StringIO()

    def emit(self, record):
        msg = self.format(record)
        self.stream.write(msg + '\n')

    def get_contents(self):
        return self.stream.getvalue()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
string_io_handler = StringIOHandler()
logger.addHandler(string_io_handler)

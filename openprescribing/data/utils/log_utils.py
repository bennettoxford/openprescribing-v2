import datetime
import logging


class LogHandler:
    def __init__(self, writer, max_name_width=0):
        self.writer = writer
        self.max_name_width = max_name_width

        root_module = __name__.partition(".")[0]
        self.logger = logging.getLogger(root_module)
        self.log_handler = logging.Handler()
        self.log_handler.emit = self.emit
        self.current_name = None

    def emit(self, record):
        self.write(self.log_handler.format(record))

    def write(self, line):
        self.writer(
            f"{datetime.datetime.now(datetime.UTC):%Y-%m-%dT%H:%M:%S} "
            f"[{self.current_name.rjust(self.max_name_width)}] "
            f"{line}"
        )

    def capture_logs_as(self, name):
        self.current_name = name
        return self

    def __enter__(self):
        self.logger.setLevel("DEBUG")
        self.logger.addHandler(self.log_handler)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.logger.removeHandler(self.log_handler)

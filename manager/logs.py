import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler


def configure(file_name, file_level=logging.DEBUG, console_level=logging.DEBUG):
    # create handlers
    log_filename = 'logs/%s' % file_name
    fh = RotatingFileHandler(filename=log_filename, backupCount=10, maxBytes=50000)
    fh.setLevel(file_level)

    ch = StreamHandler()
    ch.setLevel(console_level)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(threadName)s\n\t%(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Save Configured Handlers
    logging.basicConfig(handlers=[fh, ch])

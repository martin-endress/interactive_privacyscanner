import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

CONSOLE_LEVEL = logging.DEBUG
FILE_LEVEL = logging.INFO


def configure(file_name):
    # create handlers
    log_filename = 'logs/%s' % file_name
    fh = RotatingFileHandler(filename=log_filename, backupCount=10, maxBytes=50000)
    fh.setLevel(FILE_LEVEL)

    ch = StreamHandler()
    ch.setLevel(CONSOLE_LEVEL)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(threadName)s\n\t%(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Save Configured Handlers
    logging.basicConfig(handlers=[fh, ch])


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(CONSOLE_LEVEL)
    return logger

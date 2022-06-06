import configparser
from pathlib import Path

import errors
import logs

CONFIG_FILE = 'manager.cfg'
logger = logs.get_logger('config')


def __getattr__(name):
    if not Path(CONFIG_FILE).exists():
        msg = 'CONFIG FILE DOES NOT EXIST. Please create "manager/manager.cfg" from the template.'
        logger.error(msg)
        raise errors.ScannerInitError(msg)

    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE)
    return cfg[name]

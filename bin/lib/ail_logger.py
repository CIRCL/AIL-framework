#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import copy
import json
import sys
import logging
import logging.handlers
import unicodedata

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

LOGGING_CONF_DIR = os.path.join(os.environ['AIL_HOME'], 'configs')
LOGS_DIR = os.path.join(os.environ['AIL_HOME'], 'logs')


def _escape_access_log_value(value):
    escaped = []
    for character in str(value):
        category = unicodedata.category(character)
        if category == 'Cc' or category in {'Zl', 'Zp'}:
            escaped.append(f'\\x{ord(character):02x}')
        else:
            escaped.append(character)
    return ''.join(escaped)


class AccessLogSingleLineFormatter(logging.Formatter):

    def format(self, record):
        sanitized = copy.copy(record)
        sanitized.msg = _escape_access_log_value(record.getMessage())
        sanitized.args = ()
        for field in ('user_id', 'ip_address', 'user_agent'):
            setattr(sanitized, field, _escape_access_log_value(getattr(record, field, '-')))
        return _escape_access_log_value(super().format(sanitized))

def get_config(name=None):
    if not name:
        name = 'ail.log'
    else:
        name = f'{name}.log'
    with open(os.path.join(LOGGING_CONF_DIR, f'logging.json'), 'r') as f:
        config = json.load(f)
        config['handlers']['file']['filename'] = os.path.join(LOGS_DIR, name)
    return config

def get_access_config(create=False):
    logger = logging.getLogger('access.log')

    if create:
        formatter = AccessLogSingleLineFormatter('%(asctime)s - %(ip_address)s - %(user_agent)s - %(levelname)s - %(user_id)s - %(message)s')

        # STDOUT
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # FILE
        handler = logging.handlers.RotatingFileHandler(filename=os.path.join(LOGS_DIR, f'access.log'),
                                                       maxBytes=10*1024*1024, backupCount=5)
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.propagate = False
    return logger

def get_test_config(create=False):
    logger = logging.getLogger('test.log')

    if create:
        formatter = logging.Formatter("%(asctime)s %(levelname)s:%(message)s")

        # STDOUT
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

        # FILE
        handler = logging.handlers.RotatingFileHandler(filename=os.path.join(LOGS_DIR, f'test.log'),
                                                       maxBytes=10*1024*1024, backupCount=5)
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.propagate = False
    return logger

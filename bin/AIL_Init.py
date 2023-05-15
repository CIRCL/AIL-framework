#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
AIL Init
============================

Init DB + Clear Stats

"""

import os
import sys
import logging.config

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib import ail_queues
from lib import ail_logger

logging.config.dictConfig(ail_logger.get_config(name='modules'))
logger = logging.getLogger()

if __name__ == "__main__":
    ail_queues.save_queue_digraph()
    ail_queues.clear_modules_queues_stats()

    # Send module state to logs
    ail_uuid = ail_core.get_ail_uuid()
    logger.warning(f"AIL {ail_uuid} started")

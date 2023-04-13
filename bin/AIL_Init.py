#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
AIL Init
============================

Init DB + Clear Stats

"""

import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_queues

if __name__ == "__main__":
    ail_queues.save_queue_digraph()
    ail_queues.clear_modules_queues_stats()

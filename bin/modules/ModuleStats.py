#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    This module makes statistics for some modules and providers

"""

##################################
# Import External packages       #
##################################
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages        #
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Items import Item
from lib import Statistics


class ModuleStats(AbstractModule):
    """
    Module Statistics module for AIL framework
    """

    def __init__(self):

        super(ModuleStats, self).__init__()

        # Waiting time in seconds between to message processed
        self.pending_seconds = 20

    def compute(self, message):

        # MODULE STATS
        if len(message.split(';')) > 1:
            module_name, num, keyword, date = message.split(';')
            Statistics.update_module_stats(module_name, num, keyword, date)
        # ITEM STATS
        else:
            item_id = message
            item = Item(item_id)
            source = item.get_source()
            date = item.get_date()
            size = item.get_size()
            Statistics.update_item_stats_size_nb(item_id, source, size, date)


if __name__ == '__main__':

    module = ModuleStats()
    module.run()

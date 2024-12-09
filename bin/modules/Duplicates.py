#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Duplicate module
====================

This huge module is, in short term, checking duplicates.
Its input comes from other modules, namely:
    Credential

Perform comparisions with ssdeep and tlsh

"""

import os
import sys
import time

# from datetime import datetime, timedelta
import datetime

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import Duplicate


class Duplicates(AbstractModule):
    """Duplicates module."""

    def __init__(self):
        super(Duplicates, self).__init__()

        config_loader = ConfigLoader()
        THRESHOLD_SSDEEP = config_loader.get_config_int('Modules_Duplicates', 'threshold_duplicate_ssdeep')
        THRESHOLD_TLSH = config_loader.get_config_int('Modules_Duplicates', 'threshold_duplicate_tlsh')
        self.min_item_size = float(config_loader.get_config_str('Modules_Duplicates', 'min_paste_size')) # # TODO: # FIXME: rename me
        self.maximum_month_range = config_loader.get_config_int('Modules_Duplicates', 'maximum_month_range')

        self.algos = {
                        "ssdeep": {"threshold": THRESHOLD_SSDEEP},
                        "tlsh": {"threshold": THRESHOLD_TLSH}
                     }

        self.logger.info(f"Module: {self.module_name} Launched")

    def compute(self, message):
        # IOError: "CRC Checksum Failed on : {id}"

        item = self.get_obj()

        # Check file size
        if item.get_size() < self.min_item_size:
            return None

        # one month
        curr_date_ymonth = datetime.datetime.now().strftime("%Y%m")
        last_month_dates = Duplicate.get_last_x_month_dates(self.maximum_month_range)

        x = time.time()

        # Get Hashs
        content = item.get_content(r_type='bytes')
        self.algos['ssdeep']['hash'] = Duplicate.get_ssdeep_hash(content)
        self.algos['tlsh']['hash'] = Duplicate.get_tlsh_hash(content)

        # TODO: Handle computed duplicates

        nb_duplicates = 0

        for algo in self.algos:
            obj_hash = self.algos[algo]['hash']
            for date_ymonth in last_month_dates:
                if Duplicate.exists_algo_hash_by_month(algo, obj_hash, date_ymonth):
                    Duplicate.add_duplicate(algo, obj_hash, 100, 'item', '', item.get_id(), date_ymonth)
                    nb_duplicates += 1
                else:
                    for hash in Duplicate.get_algo_hashs_by_month(algo, date_ymonth):
                        # # FIXME:  try - catch 'hash not comparable, bad hash: '+dico_hash+' , current_hash: '+paste_hash
                        similarity = Duplicate.get_algo_similarity(algo, obj_hash, hash)
                        print(f'[{algo}] comparing: {obj_hash} and {hash} similarity: {similarity}')  # DEBUG:
                        if similarity >= self.algos[algo]['threshold']:
                            Duplicate.add_duplicate(algo, hash, similarity, 'item', '', item.get_id(), date_ymonth)
                            nb_duplicates += 1

            # Save Hashs
            Duplicate.save_object_hash(algo, curr_date_ymonth, self.algos[algo]['hash'], item.get_id())

        if nb_duplicates:
            self.logger.info(f'Duplicates {nb_duplicates};{self.obj.get_global_id()}')

        y = time.time()
        print(f'{self.obj.get_global_id()} Processed in {y-x} sec')
        # self.logger.debug('{}Processed in {} sec'.format(to_print, y-x))


if __name__ == "__main__":

    module = Duplicates()
    module.run()

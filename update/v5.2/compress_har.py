#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import gzip
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_updates
from lib import crawlers

if __name__ == '__main__':
    update = ail_updates.AILBackgroundUpdate('v5.2')
    HAR_DIR = crawlers.HAR_DIR
    hars_ids = crawlers.get_all_har_ids()
    update.set_nb_to_update(len(hars_ids))
    n = 0
    for har_id in hars_ids:
        crawlers._gzip_har(har_id)
        update.inc_nb_updated()
        if n % 100 == 0:
            update.update_progress()

    crawlers._gzip_all_hars()

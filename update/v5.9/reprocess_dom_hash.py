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
from lib.objects import ail_objects
from lib.objects import DomHashs
from lib.objects.Domains import Domain

if __name__ == '__main__':
    update = ail_updates.AILBackgroundUpdate('v5.9')
    n = 0
    nb_items = ail_objects.card_obj_iterator('item', filters={'sources': ['crawled']})
    update.set_nb_to_update(nb_items)

    for item in ail_objects.obj_iterator('item', filters={'sources': ['crawled']}):
        dom = item.get_domain()
        domain = Domain(dom)
        i_content = item.get_content()
        if domain.exists() and i_content:
            date = item.get_date()
            # DOM-HASH
            dom_hash = DomHashs.create(i_content)
            dom_hash.add(date, item)
            dom_hash.add_correlation('domain', '', domain.id)

            print(domain.id, item.id, dom_hash.id)

            update.inc_nb_updated()
            n += 1
            if n % 100 == 0:
                update.update_progress()

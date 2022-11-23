#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import argparse

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_updates

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AIL default update')
    parser.add_argument('-t', help='version tag', type=str, dest='tag', required=True)
    args = parser.parse_args()

    if not args.tag:
        parser.print_help()
        sys.exit(0)

    # remove space
    update_tag = args.tag.replace(' ', '')
    if not ail_updates.check_version(update_tag):
        parser.print_help()
        print(f'Error: Invalid update tag {update_tag}')
        sys.exit(0)

    start_deb = time.time()

    ail_updates.add_ail_update(update_tag)

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import argparse

# # TODO: check max update
max_update = 3.5

def check_version(version):
    if version[0] == 'v' and '.' in version:
        try:
            res = float(version[1:])
            if res >= 1 and res <= max_update:
                return True
        except:
            pass
    print(f'ERROR: invalid version/tag: {version}')
    return False

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Trigger backgroud update')
    parser.add_argument('-v', '--version', help='update version (tag) ex: v3.5', type=str, dest='version', required=True, default=None)
    args = parser.parse_args()

    if args.version is None:
        parser.print_help()
        sys.exit(0)
    version = args.version
    if not check_version(version):
        sys.exit(0)

    update_db_dir = os.path.join(os.environ['AIL_HOME'], 'update', version)
    update_db_script = os.path.join(update_db_dir, 'Update.py')
    if not os.path.isfile(update_db_script):
        # # TODO: launch default update
        print('DB Up To Date')
    else:
        # import Updater clas
        sys.path.append(update_db_dir)
        from Update import Updater
        updater = Updater(version)
        updater.run_update()

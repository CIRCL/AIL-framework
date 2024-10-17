#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import datetime
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

# # # # # # # #
#             #
#   UPDATE    #
#             #
# # # # # # # #

def get_ail_version():
    return r_db.get('ail:version')

def get_ail_float_version():
    version = get_ail_version()
    if version:
        version = float(version[1:])
    else:
        version = 0
    return version

# # # - - # # #

# # # # # # # # # # # #
#                     #
#  UPDATE BACKGROUND  #
#                     #
# # # # # # # # # # # #


BACKGROUND_UPDATES = {
    'v5.2': {
        'message': 'Compress HAR',
        'scripts': ['compress_har.py']
    },
    'v5.9': {
        'message': 'Compute Domain/Items Dom-Hash',
        'scripts': ['reprocess_dom_hash.py']
    }
}

class AILBackgroundUpdate:
    """
        AIL Background Update.
    """

    def __init__(self, version):
        self.version = version

    def _get_field(self, field):
        return r_db.hget('ail:update:background', field)

    def _set_field(self, field, value):
        r_db.hset('ail:update:background', field, value)

    def get_version(self):
        return self.version

    def get_message(self):
        return BACKGROUND_UPDATES.get(self.version, {}).get('message', '')

    def get_error(self):
        return self._get_field('error')

    def set_error(self, error):  # TODO ADD LOGS
        self._set_field('error', error)

    def get_nb_scripts(self):
        return int(len(BACKGROUND_UPDATES.get(self.version, {}).get('scripts', [''])))

    def get_scripts(self):
        return BACKGROUND_UPDATES.get(self.version, {}).get('scripts', [])

    def get_nb_scripts_done(self):
        done = self._get_field('done')
        try:
            done = int(done)
        except (TypeError, ValueError):
            done = 0
        return done

    def inc_nb_scripts_done(self):
        self._set_field('done', self.get_nb_scripts_done() + 1)

    def get_script(self):
        return self._get_field('script')

    def get_script_path(self):
        path = os.path.basename(self.get_script())
        if path:
            return os.path.join(os.environ['AIL_HOME'], 'update', self.version, path)

    def get_nb_to_update(self):  # TODO use cache ?????
        nb_to_update = self._get_field('nb_to_update')
        if not nb_to_update:
            nb_to_update = 1
        return int(nb_to_update)

    def set_nb_to_update(self, nb):
        self._set_field('nb_to_update', int(nb))

    def get_nb_updated(self):  # TODO use cache ?????
        nb_updated = self._get_field('nb_updated')
        if not nb_updated:
            nb_updated = 0
        return int(nb_updated)

    def inc_nb_updated(self):  # TODO use cache ?????
        r_db.hincrby('ail:update:background', 'nb_updated', 1)

    def get_progress(self):  # TODO use cache ?????
        return self._get_field('progress')

    def set_progress(self, progress):
        self._set_field('progress', progress)

    def update_progress(self):
        nb_updated = self.get_nb_updated()
        nb_to_update = self.get_nb_to_update()
        if nb_updated == nb_to_update:
            progress = 100
        elif nb_updated > nb_to_update:
            progress = 99
        else:
            progress = int((nb_updated * 100) / nb_to_update)
        self.set_progress(progress)
        print(f'{nb_updated}/{nb_to_update}    updated    {progress}%')
        return progress

    def is_running(self):
        return r_db.hget('ail:update:background', 'version') == self.version

    def get_meta(self, options=set()):
        meta = {'version': self.get_version(),
                'error': self.get_error(),
                'script': self.get_script(),
                'script_progress': self.get_progress(),
                'nb_update': self.get_nb_scripts(),
                'nb_completed': self.get_nb_scripts_done()}
        meta['progress'] = int(meta['nb_completed'] * 100 / meta['nb_update'])
        if 'message' in options:
            meta['message'] = self.get_message()
        return meta

    def start(self):
        self._set_field('version', self.version)
        r_db.hdel('ail:update:background', 'error')

    def start_script(self, script):
        self.clear()
        self._set_field('script', script)
        self.set_progress(0)

    def end_script(self):
        self.set_progress(100)
        self.inc_nb_scripts_done()

    def clear(self):
        r_db.hdel('ail:update:background', 'error')
        r_db.hdel('ail:update:background', 'progress')
        r_db.hdel('ail:update:background', 'nb_updated')
        r_db.hdel('ail:update:background', 'nb_to_update')

    def end(self):
        r_db.delete('ail:update:background')
        r_db.srem('ail:updates:background', self.version)


# To Add in update script
def add_background_update(version):
    r_db.sadd('ail:updates:background', version)

def is_update_background_running():
    return r_db.exists('ail:update:background')

def get_update_background_version():
    return r_db.hget('ail:update:background', 'version')

def get_update_background_meta(options=set()):
    version = get_update_background_version()
    if version:
        return AILBackgroundUpdate(version).get_meta(options=options)
    else:
        return {}

def get_update_background_to_launch():
    to_launch = []
    updates = r_db.smembers('ail:updates:background')
    for version in BACKGROUND_UPDATES:
        if version in updates:
            to_launch.append(version)
    return to_launch

# # # - - # # #

##########################################################################################
##########################################################################################
##########################################################################################

def get_ail_all_updates(date_separator='-'):
    dict_update = r_db.hgetall('ail:update_date')
    if date_separator:
        for version in dict_update:
            u_date = dict_update[version]
            dict_update[version] = f'{u_date[0:4]}{date_separator}{u_date[4:6]}{date_separator}{u_date[6:8]}'
    return dict_update


def add_ail_update(version):
    # Add new AIL version
    r_db.hset('ail:update_date', version, datetime.datetime.now().strftime("%Y%m%d"))
    # Set current ail version
    if float(version[1:]) > get_ail_float_version():
        r_db.set('ail:version', version)


def check_version(version):
    if version[0] != 'v':
        return False
    try:
        int(version[1])
        int(version[-1])
        int(version[1:].replace('.', ''))
    except:
        return False
    if '..' in version:
        return False
    return True


if __name__ == '__main__':
    res = check_version('v3.1..1')
    print(res)

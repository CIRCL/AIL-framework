#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The ZMQ_Feed_Q Module
=====================

This module is consuming the Redis-list created by the ZMQ_Feed_Q Module,
And save the paste on disk to allow others modules to work on them.

..todo:: Be able to choose to delete or not the saved paste after processing.
..todo:: Store the empty paste (unprocessed) somewhere in Redis.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances.
*Need the ZMQ_Feed_Q Module running to be able to work properly.

"""
import base64
import hashlib
import io
import gzip
import os
import sys
import time
import uuid

import datetime
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

from pubsublogger import publisher

from Helper import Process

config_loader = ConfigLoader.ConfigLoader()
r_stats = config_loader.get_redis_conn("ARDB_Statistics")
config_loader = None

def gunzip_bytes_obj(bytes_obj):
    in_ = io.BytesIO()
    in_.write(bytes_obj)
    in_.seek(0)
    with gzip.GzipFile(fileobj=in_, mode='rb') as fo:
        gunzipped_bytes_obj = fo.read()
    return gunzipped_bytes_obj

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


if __name__ == '__main__':
    publisher.port = 6380
    publisher.channel = 'Script'
    processed_paste = 0
    time_1 = time.time()

    config_section = 'Global'

    p = Process(config_section)

    # get and sanityze PASTE DIRECTORY
    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], p.config.get("Directories", "pastes"))
    PASTES_FOLDERS = PASTES_FOLDER + '/'
    PASTES_FOLDERS = os.path.join(os.path.realpath(PASTES_FOLDERS), '')

    # LOGGING #
    publisher.info("Feed Script started to receive & publish.")

    while True:

        message = p.get_from_set()
        # Recovering the streamed message informations.
        if message is not None:
            splitted = message.split()
            if len(splitted) == 2:
                paste, gzip64encoded = splitted
            else:
                # TODO Store the name of the empty paste inside a Redis-list.
                print("Empty Paste: not processed")
                publisher.debug("Empty Paste: {0} not processed".format(message))
                continue
        else:
            #print("Empty Queues: Waiting...")
            if int(time.time() - time_1) > 30:
                to_print = 'Global; ; ; ;glob Processed {0} paste(s) in {1} s'.format(processed_paste, time.time() - time_1)
                print(to_print)
                #publisher.info(to_print)
                time_1 = time.time()
                processed_paste = 0
            time.sleep(1)
            continue

        # remove PASTES_FOLDER from item path (crawled item + submited)
        if PASTES_FOLDERS in paste:
            paste = paste.replace(PASTES_FOLDERS, '', 1)

        file_name_paste = paste.split('/')[-1]
        if len(file_name_paste)>255:
            new_file_name_paste = '{}{}.gz'.format(file_name_paste[:215], str(uuid.uuid4()))
            paste = rreplace(paste, file_name_paste, new_file_name_paste, 1)

        # Creating the full filepath
        filename = os.path.join(PASTES_FOLDER, paste)
        filename = os.path.realpath(filename)

        # incorrect filename
        if not os.path.commonprefix([filename, PASTES_FOLDER]) == PASTES_FOLDER:
            print('Path traversal detected {}'.format(filename))
            publisher.warning('Global; Path traversal detected')
        else:

            # decode compressed base64
            decoded = base64.standard_b64decode(gzip64encoded)

            # check if file exist
            if os.path.isfile(filename):
                print('File already exist {}'.format(filename))
                publisher.warning('Global; File already exist')

                try:
                    with gzip.open(filename, 'rb') as f:
                        curr_file_content = f.read()
                except EOFError:
                    publisher.warning('Global; Incomplete file: {}'.format(filename))
                    # save daily stats
                    r_stats.zincrby('module:Global:incomplete_file', datetime.datetime.now().strftime('%Y%m%d'), 1)
                    # discard item
                    continue
                except OSError:
                    publisher.warning('Global; Not a gzipped file: {}'.format(filename))
                    # save daily stats
                    r_stats.zincrby('module:Global:invalid_file', datetime.datetime.now().strftime('%Y%m%d'), 1)
                    # discard item
                    continue

                curr_file_md5 = hashlib.md5(curr_file_content).hexdigest()

                new_file_content = gunzip_bytes_obj(decoded)
                new_file_md5 = hashlib.md5(new_file_content).hexdigest()

                if new_file_md5 != curr_file_md5:

                    if filename.endswith('.gz'):
                        filename = '{}_{}.gz'.format(filename[:-3], new_file_md5)
                    else:
                        filename = '{}_{}'.format(filename, new_file_md5)

                    # continue if new file already exist
                    if os.path.isfile(filename):
                        print('ignore duplicated file')
                        continue

                    print('new file: {}'.format(filename))
                # ignore duplicate
                else:
                    print('ignore duplicated file')
                    continue

            # create subdir
            dirname = os.path.dirname(filename)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            with open(filename, 'wb') as f:
                f.write(decoded)

            paste = filename
            # remove PASTES_FOLDER from
            if PASTES_FOLDERS in paste:
                paste = paste.replace(PASTES_FOLDERS, '', 1)

            p.populate_set_out(paste)
            processed_paste+=1

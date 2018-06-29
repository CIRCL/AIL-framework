#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    Base64 module

    Dectect Base64 and decode it
"""
import time
import os
import datetime
import redis

from pubsublogger import publisher

from Helper import Process
from packages import Paste

import re
import base64
from hashlib import sha1
import magic
import json

import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)


def search_base64(content, message, date):
    find = False
    base64_list = re.findall(regex_base64, content)
    if(len(base64_list) > 0):

        for b64 in base64_list:
            if len(b64) >= 40 :
                decode = base64.b64decode(b64)

                type = magic.from_buffer(decode, mime=True)
                #print(type)
                #print(decode)

                find = True
                hash = sha1(decode).hexdigest()
                print(message)
                print(hash)

                data = {}
                data['name'] = hash
                data['date'] = datetime.datetime.now().strftime("%d/%m/%y")
                data['origin'] = message
                data['estimated type'] = type
                json_data = json.dumps(data)

                date_paste = '{}/{}/{}'.format(date[0:4], date[4:6], date[6:8])
                date_key = date[0:4] + date[4:6] + date[6:8]

                serv_metadata.zincrby('base64_date:'+date_key, hash, 1)

                # first time we see this hash
                if not serv_metadata.hexists('metadata_hash:'+hash, 'estimated_type'):
                    serv_metadata.hset('metadata_hash:'+hash, 'first_seen', date_paste)
                    serv_metadata.hset('metadata_hash:'+hash, 'last_seen', date_paste)
                else:
                    serv_metadata.hset('metadata_hash:'+hash, 'last_seen', date_paste)

                # first time we see this file on this paste
                if serv_metadata.zscore('base64_hash:'+hash, message) is None:
                    print('first')
                    serv_metadata.hincrby('metadata_hash:'+hash, 'nb_seen_in_all_pastes', 1)

                    serv_metadata.sadd('base64_paste:'+message, hash) # paste - hash map
                    serv_metadata.zincrby('base64_hash:'+hash, message, 1)# hash - paste map

                    # create hash metadata
                    serv_metadata.hset('metadata_hash:'+hash, 'estimated_type', type)
                    serv_metadata.sadd('hash_all_type', type)
                    serv_metadata.zincrby('base64_type:'+type, date_key, 1)

                    save_base64_as_file(decode, type, hash, json_data, id)
                    print('found {} '.format(type))
                # duplicate
                else:
                    serv_metadata.zincrby('base64_hash:'+hash, message, 1) # number of b64 on this paste

    if(find):
        publisher.warning('base64 decoded')
        #Send to duplicate
        p.populate_set_out(message, 'Duplicate')
        #send to Browse_warning_paste
        msg = ('base64;{}'.format(message))
        p.populate_set_out( msg, 'alertHandler')

        msg = 'infoleak:automatic-detection="base64";{}'.format(message)
        p.populate_set_out(msg, 'Tags')

def save_base64_as_file(decode, type, hash, json_data, id):

    local_filename_b64 = os.path.join(p.config.get("Directories", "base64"), type, hash[:2], hash)
    filename_b64 = os.path.join(os.environ['AIL_HOME'], local_filename_b64)

    filename_json = os.path.join(os.environ['AIL_HOME'],
                            p.config.get("Directories", "base64"), type, hash[:2], hash + '.json')

    dirname = os.path.dirname(filename_b64)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(filename_b64, 'wb') as f:
        f.write(decode)

    # create hash metadata
    serv_metadata.hset('metadata_hash:'+hash, 'saved_path', local_filename_b64)
    serv_metadata.hset('metadata_hash:'+hash, 'size', os.path.getsize(filename_b64))

    with open(filename_json, 'w') as f:
        f.write(json_data)




if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'Base64'

    # Setup the I/O queues
    p = Process(config_section)
    max_execution_time = p.config.getint("Base64", "max_execution_time")

    serv_metadata = redis.StrictRedis(
        host=p.config.get("ARDB_Metadata", "host"),
        port=p.config.getint("ARDB_Metadata", "port"),
        db=p.config.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    # Sent to the logging a description of the module
    publisher.info("Base64 started")

    regex_base64 = '(?:[A-Za-z0-9+/]{4}){2,}(?:[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=|[A-Za-z0-9+/][AQgw]==)'
    re.compile(regex_base64)

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:

            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        filename = message
        paste = Paste.Paste(filename)

        signal.alarm(max_execution_time)
        try:
            # Do something with the message from the queue
            #print(filename)
            content = paste.get_p_content()
            date = str(paste._get_p_date())
            search_base64(content,message, date)

        except TimeoutException:
            p.incr_module_timeout_statistic()
            print ("{0} processing timeout".format(paste.p_path))
            continue
        else:
            signal.alarm(0)

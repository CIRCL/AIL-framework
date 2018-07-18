#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    Binary module

    Dectect Binary and decode it
"""
import time
import os
import datetime
import redis

from pubsublogger import publisher

from Helper import Process
from packages import Paste

import re
from hashlib import sha1
import magic
import json

import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

def decode_binary_string(s):
    return ''.join(chr(int(s[i*8:i*8+8],2)) for i in range(len(s)//8))

def search_binary(content, message, date):
    find = False
    binary_list = re.findall(regex_binary, content)
    if(len(binary_list) > 0):

        for binary in binary_list:
            if len(binary) >= 40 :
                decode = decode_binary_string(binary).encode()
                print(decode)
                print(message)

                type = magic.from_buffer(decode, mime=True)

                find = True
                hash = sha1(decode).hexdigest()
                print(hash)

                data = {}
                data['name'] = hash
                data['date'] = datetime.datetime.now().strftime("%d/%m/%y")
                data['origin'] = message
                data['estimated type'] = type
                json_data = json.dumps(data)

                date_paste = '{}/{}/{}'.format(date[0:4], date[4:6], date[6:8])
                date_key = date[0:4] + date[4:6] + date[6:8]

                serv_metadata.zincrby('binary_date:'+date_key, hash, 1)

                # first time we see this hash
                if not serv_metadata.hexists('metadata_hash:'+hash, 'estimated_type'):
                    serv_metadata.hset('metadata_hash:'+hash, 'first_seen', date_paste)
                    serv_metadata.hset('metadata_hash:'+hash, 'last_seen', date_paste)
                else:
                    serv_metadata.hset('metadata_hash:'+hash, 'last_seen', date_paste)

                # first time we see this file encoding on this paste
                if serv_metadata.zscore('binary_hash:'+hash, message) is None:
                    print('first binary')
                    serv_metadata.hincrby('metadata_hash:'+hash, 'nb_seen_in_all_pastes', 1)

                    serv_metadata.sadd('binary_paste:'+message, hash) # paste - hash map
                    serv_metadata.zincrby('binary_hash:'+hash, message, 1)# hash - paste map

                    # create hash metadata
                    serv_metadata.hset('metadata_hash:'+hash, 'estimated_type', type)
                    serv_metadata.sadd('hash_all_type', type)
                    serv_metadata.sadd('hash_binary_all_type', type)
                    serv_metadata.zincrby('binary_type:'+type, date_key, 1)

                    save_binary_as_file(decode, type, hash, json_data, id)
                    print('found {} '.format(type))
                # duplicate
                else:
                    serv_metadata.zincrby('binary_hash:'+hash, message, 1) # number of b64 on this paste

    if(find):
        publisher.warning('binary decoded')
        #Send to duplicate
        p.populate_set_out(message, 'Duplicate')
        #send to Browse_warning_paste
        msg = ('binary;{}'.format(message))
        p.populate_set_out( msg, 'alertHandler')

        msg = 'infoleak:automatic-detection="binary";{}'.format(message)
        p.populate_set_out(msg, 'Tags')

def save_binary_as_file(decode, type, hash, json_data, id):

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
    config_section = 'Binary'

    # Setup the I/O queues
    p = Process(config_section)
    max_execution_time = p.config.getint("Binary", "max_execution_time")

    serv_metadata = redis.StrictRedis(
        host=p.config.get("ARDB_Metadata", "host"),
        port=p.config.getint("ARDB_Metadata", "port"),
        db=p.config.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    # Sent to the logging a description of the module
    publisher.info("Binary started")

    regex_binary = '[0-1]{40,}'
    re.compile(regex_binary)

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
            search_binary(content,message, date)

        except TimeoutException:
            p.incr_module_timeout_statistic()
            print ("{0} processing timeout".format(paste.p_path))
            continue
        else:
            signal.alarm(0)

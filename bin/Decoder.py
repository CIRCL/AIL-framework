#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    Decoder module

    Dectect Binary and decode it
"""
import time
import os
import redis
import base64
from hashlib import sha1
import magic
import json
import datetime

from pubsublogger import publisher

from Helper import Process
from packages import Paste

import re
import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

def hex_decoder(hexStr):
    #hexStr = ''.join( hex_string.split(" ") )
    return bytes(bytearray([int(hexStr[i:i+2], 16) for i in range(0, len(hexStr), 2)]))

def binary_decoder(binary_string):
    return bytes(bytearray([int(binary_string[i:i+8], 2) for i in range(0, len(binary_string), 8)]))

def base64_decoder(base64_string):
    return base64.b64decode(base64_string)

def decode_string(content, message, date, encoded_list, decoder_name, encoded_min_size):
    find = False
    for encoded in encoded_list:
        if len(encoded) >=  encoded_min_size:
            decode = decoder_function[decoder_name](encoded)
            find = True

            save_hash(decoder_name, message, date, decode)

            #remove encoded from paste content
            content = content.replace(encoded, '', 1)

    if(find):
        set_out_paste(decoder_name, message)

    return content

# # TODO: FIXME check db
def save_hash(decoder_name, message, date, decoded):
    print(decoder_name)
    type = magic.from_buffer(decoded, mime=True)
    hash = sha1(decoded).hexdigest()
    print(hash)

    data = {}
    data['name'] = hash
    data['date'] = datetime.datetime.now().strftime("%d/%m/%y")
    data['origin'] = message
    data['estimated type'] = type
    json_data = json.dumps(data)

    date_paste = '{}/{}/{}'.format(date[0:4], date[4:6], date[6:8])
    date_key = date[0:4] + date[4:6] + date[6:8]

    serv_metadata.incrby(decoder_name+'_decoded:'+date_key, 1)
    serv_metadata.zincrby('hash_date:'+date_key, hash, 1)
    serv_metadata.zincrby(decoder_name+'_date:'+date_key, hash, 1)

    # first time we see this hash
    if not serv_metadata.hexists('metadata_hash:'+hash, 'estimated_type'):
        serv_metadata.hset('metadata_hash:'+hash, 'first_seen', date_paste)
        serv_metadata.hset('metadata_hash:'+hash, 'last_seen', date_paste)
    else:
        serv_metadata.hset('metadata_hash:'+hash, 'last_seen', date_paste)

    # first time we see this hash (all encoding) on this paste
    if serv_metadata.zscore('nb_seen_hash:'+hash, message) is None:
        serv_metadata.hincrby('metadata_hash:'+hash, 'nb_seen_in_all_pastes', 1)
        serv_metadata.sadd('hash_paste:'+message, hash) # paste - hash map
        # create hash metadata
        serv_metadata.hset('metadata_hash:'+hash, 'estimated_type', type)
        serv_metadata.sadd('hash_all_type', type)

    # first time we see this hash encoding on this paste
    if serv_metadata.zscore(decoder_name+'_hash:'+hash, message) is None:
        print('first '+decoder_name)

        serv_metadata.sadd(decoder_name+'_paste:'+message, hash) # paste - hash map

        # create hash metadata
        serv_metadata.sadd('hash_'+ decoder_name +'_all_type', type)

        # first time we see this hash today
        #if serv_metadata.zscore('hash_date:'+date_key, hash) is None:
        #    serv_metadata.zincrby('hash_type:'+type, date_key, 1)

        # first time we see this hash encoding today
        if serv_metadata.zscore(decoder_name+'_date:'+date_key, hash) is None:
            serv_metadata.zincrby(decoder_name+'_type:'+type, date_key, 1)

        save_hash_on_disk(decoded, type, hash, json_data)
        print('found {} '.format(type))

    serv_metadata.hincrby('metadata_hash:'+hash, decoder_name+'_decoder', 1)

    serv_metadata.zincrby(decoder_name+'_type:'+type, date_key, 1)

    serv_metadata.zincrby('nb_seen_hash:'+hash, message, 1)# hash - paste map
    serv_metadata.zincrby(decoder_name+'_hash:'+hash, message, 1) # number of b64 on this paste


def save_hash_on_disk(decode, type, hash, json_data):

    local_filename_hash = os.path.join(p.config.get("Directories", "hash"), type, hash[:2], hash)
    filename_hash = os.path.join(os.environ['AIL_HOME'], local_filename_hash)

    filename_json = os.path.join(os.environ['AIL_HOME'],
                            p.config.get("Directories", "hash"), type, hash[:2], hash + '.json')

    dirname = os.path.dirname(filename_hash)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(filename_hash, 'wb') as f:
        f.write(decode)

    # create hash metadata
    serv_metadata.hset('metadata_hash:'+hash, 'saved_path', local_filename_hash)
    serv_metadata.hset('metadata_hash:'+hash, 'size', os.path.getsize(filename_hash))

    with open(filename_json, 'w') as f:
        f.write(json_data)

def set_out_paste(decoder_name, message):
    publisher.warning(decoder_name+' decoded')
    #Send to duplicate
    p.populate_set_out(message, 'Duplicate')

    msg = 'infoleak:automatic-detection="'+decoder_name+'";{}'.format(message)
    p.populate_set_out(msg, 'Tags')


if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'Decoder'

    # Setup the I/O queues
    p = Process(config_section)

    serv_metadata = redis.StrictRedis(
        host=p.config.get("ARDB_Metadata", "host"),
        port=p.config.getint("ARDB_Metadata", "port"),
        db=p.config.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    # Sent to the logging a description of the module
    publisher.info("Decoder started")

    regex_binary = '[0-1]{40,}'
    #regex_hex = '(0[xX])?[A-Fa-f0-9]{40,}'
    regex_hex = '[A-Fa-f0-9]{40,}'
    regex_base64 = '(?:[A-Za-z0-9+/]{4}){2,}(?:[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=|[A-Za-z0-9+/][AQgw]==)'

    re.compile(regex_binary)
    re.compile(regex_hex)
    re.compile(regex_base64)

    # map decoder function
    decoder_function = {'binary':binary_decoder,'hexadecimal':hex_decoder, 'base64':base64_decoder}

    hex_max_execution_time = p.config.getint("Hex", "max_execution_time")
    binary_max_execution_time = p.config.getint("Binary", "max_execution_time")
    base64_max_execution_time = p.config.getint("Base64", "max_execution_time")

    # list all decoder yith regex,
    decoder_binary = {'name': 'binary', 'regex': regex_binary, 'encoded_min_size': 300, 'max_execution_time': binary_max_execution_time}
    decoder_hexadecimal = {'name': 'hexadecimal', 'regex': regex_hex, 'encoded_min_size': 300, 'max_execution_time': hex_max_execution_time}
    decoder_base64 = {'name': 'base64', 'regex': regex_base64, 'encoded_min_size': 40, 'max_execution_time': base64_max_execution_time}

    decoder_order = [ decoder_base64, decoder_binary, decoder_hexadecimal, decoder_base64]

    for decoder in decoder_order:
        serv_metadata.sadd('all_decoder', decoder['name'])

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

        # Do something with the message from the queue
        content = paste.get_p_content()
        date = str(paste._get_p_date())

        for decoder in decoder_order: # add threshold and size limit

            # max execution time on regex
            signal.alarm(decoder['max_execution_time'])
            try:
                encoded_list = re.findall(decoder['regex'], content)
            except TimeoutException:
                encoded_list = []
                p.incr_module_timeout_statistic() # add encoder type
                print ("{0} processing timeout".format(paste.p_rel_path))
                continue
            else:
                signal.alarm(0)

                if(len(encoded_list) > 0):
                    content = decode_string(content, message, date, encoded_list, decoder['name'], decoder['encoded_min_size'])

#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    Decoder module

    Dectect Binary and decode it
"""

##################################
# Import External packages
##################################
import time
import os
import redis
import base64
from hashlib import sha1
import magic
import json
import datetime
from pubsublogger import publisher
import re
import signal
from lib import Decoded


##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from Helper import Process
from packages import Item


class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)


class Decoder(AbstractModule):
    """
    Decoder module for AIL framework
    """

    # TODO to lambda expr
    def hex_decoder(self, hexStr):
        #hexStr = ''.join( hex_string.split(" ") )
        return bytes(bytearray([int(hexStr[i:i+2], 16) for i in range(0, len(hexStr), 2)]))


    # TODO to lambda expr
    def binary_decoder(self, binary_string):
        return bytes(bytearray([int(binary_string[i:i+8], 2) for i in range(0, len(binary_string), 8)]))


    # TODO to lambda expr
    def base64_decoder(self, base64_string):
        return base64.b64decode(base64_string)


    def __init__(self):
        super(Decoder, self).__init__(logger_channel="script:decoder")

        serv_metadata = redis.StrictRedis(
            host=self.process.config.get("ARDB_Metadata", "host"),
            port=self.process.config.getint("ARDB_Metadata", "port"),
            db=self.process.config.getint("ARDB_Metadata", "db"),
            decode_responses=True)

        regex_binary = '[0-1]{40,}'
        #regex_hex = '(0[xX])?[A-Fa-f0-9]{40,}'
        regex_hex = '[A-Fa-f0-9]{40,}'
        regex_base64 = '(?:[A-Za-z0-9+/]{4}){2,}(?:[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=|[A-Za-z0-9+/][AQgw]==)'

        cmp_regex_binary = re.compile(regex_binary)
        cmp_regex_hex = re.compile(regex_hex)
        cmp_regex_base64 = re.compile(regex_base64)

        # map decoder function
        self.decoder_function = {'binary':self.binary_decoder,'hexadecimal':self.hex_decoder, 'base64':self.base64_decoder}

        hex_max_execution_time = self.process.config.getint("Hex", "max_execution_time")
        binary_max_execution_time = self.process.config.getint("Binary", "max_execution_time")
        base64_max_execution_time = self.process.config.getint("Base64", "max_execution_time")

        # list all decoder with regex,
        decoder_binary = {'name': 'binary', 'regex': cmp_regex_binary, 'encoded_min_size': 300, 'max_execution_time': binary_max_execution_time}
        decoder_hexadecimal = {'name': 'hexadecimal', 'regex': cmp_regex_hex, 'encoded_min_size': 300, 'max_execution_time': hex_max_execution_time}
        decoder_base64 = {'name': 'base64', 'regex': cmp_regex_base64, 'encoded_min_size': 40, 'max_execution_time': base64_max_execution_time}

        self.decoder_order = [ decoder_base64, decoder_binary, decoder_hexadecimal, decoder_base64]

        for decoder in self.decoder_order:
            serv_metadata.sadd('all_decoder', decoder['name'])

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 1

        # Send module state to logs
        self.redis_logger.info(f'Module {self.module_name} initialized')


    def compute(self, message):

        obj_id = Item.get_item_id(message)

        # Extract info from message
        content = Item.get_item_content(obj_id)
        date = Item.get_item_date(obj_id)

        for decoder in self.decoder_order: # add threshold and size limit
            # max execution time on regex
            signal.alarm(decoder['max_execution_time'])

            try:
                encoded_list = decoder['regex'].findall(content)
            except TimeoutException:
                encoded_list = []
                self.process.incr_module_timeout_statistic() # add encoder type
                self.redis_logger.debug(f"{obj_id} processing timeout")
                continue
            else:
                signal.alarm(0)

                if(len(encoded_list) > 0):
                    content = self.decode_string(content, message, date, encoded_list, decoder['name'], decoder['encoded_min_size'])


    def decode_string(self, content, item_id, item_date, encoded_list, decoder_name, encoded_min_size):
        find = False
        for encoded in encoded_list:
            if len(encoded) >=  encoded_min_size:
                decoded_file = self.decoder_function[decoder_name](encoded)
                find = True

                sha1_string = sha1(decoded_file).hexdigest()
                mimetype = Decoded.get_file_mimetype(decoded_file)
                if not mimetype:
                    self.redis_logger.debug(item_id)
                    self.redis_logger.debug(sha1_string)
                    raise Exception('Invalid mimetype')
                Decoded.save_decoded_file_content(sha1_string, decoded_file, item_date, mimetype=mimetype)
                Decoded.save_item_relationship(sha1_string, item_id)
                Decoded.create_decoder_matadata(sha1_string, item_id, decoder_name)

                #remove encoded from item content
                content = content.replace(encoded, '', 1)

                self.redis_logger.debug(f'{item_id} : {decoder_name} - {mimetype}')
        if(find):
            self.set_out_item(decoder_name, item_id)

        return content


    def set_out_item(self, decoder_name, item_id):

        self.redis_logger.warning(f'{decoder_name} decoded')
        
        # Send to duplicate
        self.process.populate_set_out(item_id, 'Duplicate')

        # Send to Tags
        msg = f'infoleak:automatic-detection="{decoder_name}";{item_id}'
        self.process.populate_set_out(msg, 'Tags')

if __name__ == '__main__':
    
    module = Decoder()
    module.run()

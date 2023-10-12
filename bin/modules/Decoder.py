#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    Decoder module

    Dectect Binary and decode it
"""

##################################
# Import External packages
##################################
import os
import base64
from hashlib import sha1
import re
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib.objects.Decodeds import Decoded
from trackers.Tracker_Term import Tracker_Term
from trackers.Tracker_Regex import Tracker_Regex
from trackers.Tracker_Yara import Tracker_Yara

config_loader = ConfigLoader()
hex_max_execution_time = config_loader.get_config_int("Decoder", "max_execution_time_hexadecimal")
binary_max_execution_time = config_loader.get_config_int("Decoder", "max_execution_time_binary")
base64_max_execution_time = config_loader.get_config_int("Decoder", "max_execution_time_base64")
config_loader = None


class Decoder(AbstractModule):
    """
    Decoder module for AIL framework
    """

    def hex_decoder(self, hexStr):
        # hexStr = ''.join( hex_string.split(" ") )
        return bytes(bytearray([int(hexStr[i:i+2], 16) for i in range(0, len(hexStr), 2)]))

    def binary_decoder(self, binary_string):
        return bytes(bytearray([int(binary_string[i:i+8], 2) for i in range(0, len(binary_string), 8)]))

    def base64_decoder(self, base64_string):
        return base64.b64decode(base64_string)

    def __init__(self):
        super(Decoder, self).__init__()

        regex_binary = r'[0-1]{40,}'
        # regex_hex = r'(0[xX])?[A-Fa-f0-9]{40,}'
        regex_hex = r'[A-Fa-f0-9]{40,}'
        regex_base64 = r'(?:[A-Za-z0-9+/]{4}){2,}(?:[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=|[A-Za-z0-9+/][AQgw]==)'

        cmp_regex_binary = re.compile(regex_binary)
        cmp_regex_hex = re.compile(regex_hex)
        cmp_regex_base64 = re.compile(regex_base64)

        # map decoder function
        self.decoder_function = {'binary': self.binary_decoder,
                                 'hexadecimal': self.hex_decoder,
                                 'base64': self.base64_decoder}

        # list all decoder with regex,
        decoder_binary = {'name': 'binary', 'regex': cmp_regex_binary,
                          'encoded_min_size': 300, 'max_execution_time': binary_max_execution_time}
        decoder_hexadecimal = {'name': 'hexadecimal', 'regex': cmp_regex_hex,
                               'encoded_min_size': 300, 'max_execution_time': hex_max_execution_time}
        decoder_base64 = {'name': 'base64', 'regex': cmp_regex_base64,
                          'encoded_min_size': 40, 'max_execution_time': base64_max_execution_time}

        self.decoder_order = [decoder_base64, decoder_binary, decoder_hexadecimal, decoder_base64]

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        self.tracker_term = Tracker_Term(queue=False)
        self.tracker_regex = Tracker_Regex(queue=False)
        self.tracker_yara = Tracker_Yara(queue=False)

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def compute(self, message):
        content = self.obj.get_content()
        date = self.obj.get_date()
        new_decodeds = []

        for decoder in self.decoder_order:
            find = False
            dname = decoder['name']

            encodeds = self.regex_findall(decoder['regex'], self.obj.id, content)
            # PERF remove encoded from obj content
            for encoded in encodeds:
                content = content.replace(encoded, '', 1)
            encodeds = set(encodeds)

            for encoded in encodeds:
                if len(encoded) >= decoder['encoded_min_size']:
                    find = True
                    decoded_file = self.decoder_function[dname](encoded)

                    sha1_string = sha1(decoded_file).hexdigest()
                    decoded = Decoded(sha1_string)

                    if not decoded.exists():
                        mimetype = decoded.guess_mimetype(decoded_file)
                        if not mimetype:
                            print(sha1_string, self.obj.id)
                            raise Exception(f'Invalid mimetype: {decoded.id} {self.obj.id}')
                        decoded.save_file(decoded_file, mimetype)
                        new_decodeds.append(decoded.id)
                    else:
                        mimetype = decoded.get_mimetype()
                    decoded.add(date, self.obj, dname, mimetype=mimetype)

                    # new_decodeds.append(decoded.id)
                    self.logger.info(f'{self.obj.id} : {dname} - {decoded.id} - {mimetype}')

            if find:
                self.logger.info(f'{self.obj.id} - {dname}')

                # Send to Tags
                tag = f'infoleak:automatic-detection="{dname}"'
                self.add_message_to_queue(message=tag, queue='Tags')

                ####################
                # TRACKERS DECODED
                for decoded_id in new_decodeds:
                    decoded = Decoded(decoded_id)
                    try:
                        self.tracker_term.compute_manual(decoded)
                        self.tracker_regex.compute_manual(decoded)
                    except UnicodeDecodeError:
                        pass
                    self.tracker_yara.compute_manual(decoded)


if __name__ == '__main__':
    module = Decoder()
    module.run()

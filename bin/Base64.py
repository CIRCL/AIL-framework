#!/usr/bin/env python3.5
# -*-coding:UTF-8 -*
"""
    Base64 module

    Dectect Base64, decode it and send to XXX for reprocess
"""
import time
import os

from pubsublogger import publisher

from Helper import Process
from packages import Paste

import re
import base64
from hashlib import sha1
import magic

def search_base64(content, message):
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
                save_base64_as_file(decode, type)
                print('found {} '.format(type))
    if(find):
        publisher.warning('base64 decoded')
        #Send to duplicate
        p.populate_set_out(message, 'Duplicate')
        #send to Browse_warning_paste
        msg = ('base64;{}'.format(message))
        p.populate_set_out( msg, 'alertHandler')

def save_base64_as_file(decode, type):

    hash = sha1(decode).hexdigest()

    filename = os.path.join(os.environ['AIL_HOME'],
                            p.config.get("Directories", "base64"), type, hash[:2], hash)

    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(filename, 'wb') as f:
        f.write(decode)




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

            # Do something with the message from the queue

        filename = message
        paste = Paste.Paste(filename)
        content = paste.get_p_content()

        #print(filename)
        search_base64(content,message)

        # (Optional) Send that thing to the next queue
        #p.populate_set_out(something_has_been_done)

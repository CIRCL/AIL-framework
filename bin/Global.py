#!/usr/bin/env python3.5
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
import os
import time
from pubsublogger import publisher

from Helper import Process

import magic
import io
#import gzip

'''
def gunzip_bytes_obj(bytes_obj):
    in_ = io.BytesIO()
    in_.write(bytes_obj)
    in_.seek(0)
    with gzip.GzipFile(fileobj=in_, mode='rb') as fo:
        gunzipped_bytes_obj = fo.read()

    return gunzipped_bytes_obj.decode()'''

if __name__ == '__main__':
    publisher.port = 6380
    publisher.channel = 'Script'
    processed_paste = 0
    time_1 = time.time()

    config_section = 'Global'

    p = Process(config_section)

    # LOGGING #
    publisher.info("Feed Script started to receive & publish.")

    while True:

        message = p.get_from_set()
        #print(message)
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
            print("Empty Queues: Waiting...")
            if int(time.time() - time_1) > 30:
                to_print = 'Global; ; ; ;glob Processed {0} paste(s)'.format(processed_paste)
                print(to_print)
                #publisher.info(to_print)
                time_1 = time.time()
                processed_paste = 0
            time.sleep(1)
            continue
        # Creating the full filepath
        filename = os.path.join(os.environ['AIL_HOME'],
                                p.config.get("Directories", "pastes"), paste)

        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        decoded = base64.standard_b64decode(gzip64encoded)

        with open(filename, 'wb') as f:
            f.write(decoded)
        '''try:
            decoded2 = gunzip_bytes_obj(decoded)
        except:
            decoded2 =''

        type = magic.from_buffer(decoded2, mime=True)

        if type!= 'text/x-c++' and type!= 'text/html' and type!= 'text/x-c' and type!= 'text/x-python' and type!= 'text/x-php' and type!= 'application/xml' and type!= 'text/x-shellscript' and type!= 'text/plain' and type!= 'text/x-diff' and type!= 'text/x-ruby':

            print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
            print(filename)
            print(type)
            print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
            '''
        p.populate_set_out(filename)
        processed_paste+=1

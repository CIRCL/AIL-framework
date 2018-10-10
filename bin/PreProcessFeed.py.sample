#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
The preProcess Module
=====================

This module is just an example of how we can pre-process a feed coming from the Mixer
module before seding it to the Global module.

'''

import time
from pubsublogger import publisher

from Helper import Process


def do_something(message):
    splitted = message.split()
    if len(splitted) == 2:
        paste_name, gzip64encoded = splitted

    paste_name = paste_name.replace("pastebin", "pastebinPROCESSED")

    to_send = "{0} {1}".format(paste_name, gzip64encoded)
    return to_send

if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'PreProcessFeed'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("<description of the module>")

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            print("queue empty")
            time.sleep(1)
            continue

        # Do something with the message from the queue
        new_message = do_something(message)

        # (Optional) Send that thing to the next queue
        p.populate_set_out(new_message)

#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
    Template for new modules
"""

import time
from pubsublogger import publisher

from Helper import Process
from packages import Paste


def search_gpg(message):
    paste = Paste.Paste(message)
    content = paste.get_p_content()
    if '-----BEGIN PGP MESSAGE-----' in content:
        publisher.warning('{} has a PGP enc message'.format(paste.p_name))


if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'Keys'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Run Keys module ")

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        search_gpg(message)

        # (Optional) Send that thing to the next queue
        #p.populate_set_out(something_has_been_done)

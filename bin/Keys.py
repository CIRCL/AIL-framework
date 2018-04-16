#!/usr/bin/env python3.5
# -*-coding:UTF-8 -*

"""
The Keys Module
======================

This module is consuming the Redis-list created by the Global module.

It is looking for PGP, private and encrypted private,
RSA private key, certificate messages

"""

import time
from pubsublogger import publisher

#from bin.packages import Paste
#from bin.Helper import Process

from packages import Paste
from Helper import Process


def search_key(paste):
    content = paste.get_p_content()
    find = False
    if '-----BEGIN PGP MESSAGE-----' in content:
        publisher.warning('{} has a PGP enc message'.format(paste.p_name))
        find = True

    if '-----BEGIN CERTIFICATE-----' in content:
        publisher.warning('{} has a certificate message'.format(paste.p_name))
        find = True

    if '-----BEGIN RSA PRIVATE KEY-----' in content:
        publisher.warning('{} has a RSA private key message'.format(paste.p_name))
        find = True

    if '-----BEGIN PRIVATE KEY-----' in content:
        publisher.warning('{} has a private key message'.format(paste.p_name))
        find = True

    if '-----BEGIN ENCRYPTED PRIVATE KEY-----' in content:
        publisher.warning('{} has an encrypted private key message'.format(paste.p_name))
        find = True

    if '-----BEGIN OPENSSH PRIVATE KEY-----' in content:
        publisher.warning('{} has an openssh private key message'.format(paste.p_name))
        find = True

    if '-----BEGIN DSA PRIVATE KEY-----' in content:
        publisher.warning('{} has a dsa private key message'.format(paste.p_name))
        find = True

    if '-----BEGIN EC PRIVATE KEY-----' in content:
        publisher.warning('{} has an ec private key message'.format(paste.p_name))
        find = True

    if '-----BEGIN PGP PRIVATE KEY BLOCK-----' in content:
        publisher.warning('{} has a pgp private key block message'.format(paste.p_name))
        find = True

    if find :

        #Send to duplicate
        p.populate_set_out(message, 'Duplicate')
        #send to Browse_warning_paste
        msg = ('keys;{}'.format(message))
        print(message)
        p.populate_set_out( msg, 'alertHandler')


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
        paste = Paste.Paste(message)
        search_key(paste)

        # (Optional) Send that thing to the next queue

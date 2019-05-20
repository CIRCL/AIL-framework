#!/usr/bin/env python3
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
    get_pgp_content = False
    if '-----BEGIN PGP MESSAGE-----' in content:
        publisher.warning('{} has a PGP enc message'.format(paste.p_name))

        msg = 'infoleak:automatic-detection="pgp-message";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        get_pgp_content = True
        find = True

    if '-----BEGIN PGP PUBLIC KEY BLOCK-----' in content:
        msg = 'infoleak:automatic-detection="pgp-public-key-block";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        get_pgp_content = True

    if '-----BEGIN PGP SIGNATURE-----' in content:
        msg = 'infoleak:automatic-detection="pgp-signature";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        get_pgp_content = True


    if '-----BEGIN CERTIFICATE-----' in content:
        publisher.warning('{} has a certificate message'.format(paste.p_name))

        msg = 'infoleak:automatic-detection="certificate";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        find = True

    if '-----BEGIN RSA PRIVATE KEY-----' in content:
        publisher.warning('{} has a RSA private key message'.format(paste.p_name))
        print('rsa private key message found')

        msg = 'infoleak:automatic-detection="rsa-private-key";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        find = True

    if '-----BEGIN PRIVATE KEY-----' in content:
        publisher.warning('{} has a private key message'.format(paste.p_name))
        print('private key message found')

        msg = 'infoleak:automatic-detection="private-key";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        find = True

    if '-----BEGIN ENCRYPTED PRIVATE KEY-----' in content:
        publisher.warning('{} has an encrypted private key message'.format(paste.p_name))
        print('encrypted private key message found')

        msg = 'infoleak:automatic-detection="encrypted-private-key";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        find = True

    if '-----BEGIN OPENSSH PRIVATE KEY-----' in content:
        publisher.warning('{} has an openssh private key message'.format(paste.p_name))
        print('openssh private key message found')

        msg = 'infoleak:automatic-detection="private-ssh-key";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        find = True

    if '---- BEGIN SSH2 ENCRYPTED PRIVATE KEY ----' in content:
        publisher.warning('{} has an ssh2 private key message'.format(paste.p_name))
        print('SSH2 private key message found')

        msg = 'infoleak:automatic-detection="private-ssh-key";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        find = True

    if '-----BEGIN OpenVPN Static key V1-----' in content:
        publisher.warning('{} has an openssh private key message'.format(paste.p_name))
        print('OpenVPN Static key message found')

        msg = 'infoleak:automatic-detection="vpn-static-key";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        find = True

    if '-----BEGIN DSA PRIVATE KEY-----' in content:
        publisher.warning('{} has a dsa private key message'.format(paste.p_name))

        msg = 'infoleak:automatic-detection="dsa-private-key";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        find = True

    if '-----BEGIN EC PRIVATE KEY-----' in content:
        publisher.warning('{} has an ec private key message'.format(paste.p_name))

        msg = 'infoleak:automatic-detection="ec-private-key";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        find = True

    if '-----BEGIN PGP PRIVATE KEY BLOCK-----' in content:
        publisher.warning('{} has a pgp private key block message'.format(paste.p_name))

        msg = 'infoleak:automatic-detection="pgp-private-key";{}'.format(message)
        p.populate_set_out(msg, 'Tags')
        find = True

    # pgp content
    if get_pgp_content:
        p.populate_set_out(message, 'PgpDump')

    if find :

        #Send to duplicate
        p.populate_set_out(message, 'Duplicate')
        print(message)


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

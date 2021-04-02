#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Keys Module
======================

This module is consuming the Redis-list created by the Global module.

It is looking for PGP, private and encrypted private,
RSA private key, certificate messages

"""

##################################
# Import External packages
##################################
import time
from enum import Enum
from pubsublogger import publisher


##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from packages import Paste
from Helper import Process


class KeyEnum(Enum):
    PGP_MESSAGE = '-----BEGIN PGP MESSAGE-----'
    PGP_PUBLIC_KEY_BLOCK = '-----BEGIN PGP PUBLIC KEY BLOCK-----'
    PGP_PRIVATE_KEY_BLOCK = '-----BEGIN PGP PRIVATE KEY BLOCK-----'
    PGP_SIGNATURE = '-----BEGIN PGP SIGNATURE-----'
    CERTIFICATE = '-----BEGIN CERTIFICATE-----'
    PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----'
    PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----'
    ENCRYPTED_PRIVATE_KEY = '-----BEGIN ENCRYPTED PRIVATE KEY-----'
    OPENSSH_PRIVATE_KEY = '-----BEGIN OPENSSH PRIVATE KEY-----'
    SSH2_ENCRYPTED_PRIVATE_KEY = '---- BEGIN SSH2 ENCRYPTED PRIVATE KEY ----'
    OPENVPN_STATIC_KEY_V1 = '-----BEGIN OpenVPN Static key V1-----'
    RSA_PRIVATE_KEY = '-----BEGIN RSA PRIVATE KEY-----'
    DSA_PRIVATE_KEY = '-----BEGIN DSA PRIVATE KEY-----'
    EC_PRIVATE_KEY = '-----BEGIN EC PRIVATE KEY-----'


class Keys(AbstractModule):
    """
    Keys module for AIL framework
    """
    
    def __init__(self):
        super(Keys, self).__init__()

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 1


    def compute(self, message):
        paste = Paste.Paste(message)
        content = paste.get_p_content()

        find = False
        get_pgp_content = False

        if KeyEnum.PGP_MESSAGE.value in content:
            self.redis_logger.warning('{} has a PGP enc message'.format(paste.p_name))

            msg = 'infoleak:automatic-detection="pgp-message";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            get_pgp_content = True
            find = True

        if KeyEnum.PGP_PUBLIC_KEY_BLOCK.value in content:
            msg = 'infoleak:automatic-detection="pgp-public-key-block";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            get_pgp_content = True

        if KeyEnum.PGP_SIGNATURE.value in content:
            msg = 'infoleak:automatic-detection="pgp-signature";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            get_pgp_content = True

        if KeyEnum.CERTIFICATE.value in content:
            self.redis_logger.warning('{} has a certificate message'.format(paste.p_name))

            msg = 'infoleak:automatic-detection="certificate";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        if KeyEnum.RSA_PRIVATE_KEY.value in content:
            self.redis_logger.warning('{} has a RSA private key message'.format(paste.p_name))
            print('rsa private key message found')

            msg = 'infoleak:automatic-detection="rsa-private-key";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        if KeyEnum.PRIVATE_KEY.value in content:
            self.redis_logger.warning('{} has a private key message'.format(paste.p_name))
            print('private key message found')

            msg = 'infoleak:automatic-detection="private-key";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        if KeyEnum.ENCRYPTED_PRIVATE_KEY.value in content:
            self.redis_logger.warning('{} has an encrypted private key message'.format(paste.p_name))
            print('encrypted private key message found')

            msg = 'infoleak:automatic-detection="encrypted-private-key";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        if KeyEnum.OPENSSH_PRIVATE_KEY.value in content:
            self.redis_logger.warning('{} has an openssh private key message'.format(paste.p_name))
            print('openssh private key message found')

            msg = 'infoleak:automatic-detection="private-ssh-key";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        if KeyEnum.SSH2_ENCRYPTED_PRIVATE_KEY.value in content:
            self.redis_logger.warning('{} has an ssh2 private key message'.format(paste.p_name))
            print('SSH2 private key message found')

            msg = 'infoleak:automatic-detection="private-ssh-key";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        if KeyEnum.OPENVPN_STATIC_KEY_V1.value in content:
            self.redis_logger.warning('{} has an openssh private key message'.format(paste.p_name))
            print('OpenVPN Static key message found')

            msg = 'infoleak:automatic-detection="vpn-static-key";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        if KeyEnum.DSA_PRIVATE_KEY.value in content:
            self.redis_logger.warning('{} has a dsa private key message'.format(paste.p_name))

            msg = 'infoleak:automatic-detection="dsa-private-key";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        if KeyEnum.EC_PRIVATE_KEY.value in content:
            self.redis_logger.warning('{} has an ec private key message'.format(paste.p_name))

            msg = 'infoleak:automatic-detection="ec-private-key";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        if KeyEnum.PGP_PRIVATE_KEY_BLOCK.value in content:
            self.redis_logger.warning('{} has a pgp private key block message'.format(paste.p_name))

            msg = 'infoleak:automatic-detection="pgp-private-key";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        if KeyEnum.PUBLIC_KEY.value in content:
            self.redis_logger.warning('{} has a public key message'.format(paste.p_name))

            msg = 'infoleak:automatic-detection="public-key";{}'.format(message)
            self.process.populate_set_out(msg, 'Tags')
            find = True

        # pgp content
        if get_pgp_content:
            self.process.populate_set_out(message, 'PgpDump')

        if find :
            #Send to duplicate
            self.process.populate_set_out(message, 'Duplicate')
            self.redis_logger.debug(message)


if __name__ == '__main__':
        
    module = Keys()
    module.run()

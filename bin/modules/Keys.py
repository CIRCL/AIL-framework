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
import os
import sys
from enum import Enum

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule


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

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

    def compute(self, message):
        obj = self.get_obj()
        content = obj.get_content()

        # find = False
        get_pgp_content = False

        if KeyEnum.PGP_MESSAGE.value in content:
            print(f'{self.obj.get_global_id()} has a PGP enc message')

            tag = 'infoleak:automatic-detection="pgp-message"'
            self.add_message_to_queue(message=tag, queue='Tags')
            get_pgp_content = True
            # find = True

        if KeyEnum.PGP_PUBLIC_KEY_BLOCK.value in content:
            tag = 'infoleak:automatic-detection="pgp-public-key-block"'
            self.add_message_to_queue(message=tag, queue='Tags')
            get_pgp_content = True

        if KeyEnum.PGP_SIGNATURE.value in content:
            tag = 'infoleak:automatic-detection="pgp-signature"'
            self.add_message_to_queue(message=tag, queue='Tags')
            get_pgp_content = True

        if KeyEnum.PGP_PRIVATE_KEY_BLOCK.value in content:
            print(f'{self.obj.get_global_id()} has a pgp private key block message')

            tag = 'infoleak:automatic-detection="pgp-private-key"'
            self.add_message_to_queue(message=tag, queue='Tags')
            get_pgp_content = True

        if KeyEnum.CERTIFICATE.value in content:
            print(f'{self.obj.get_global_id()} has a certificate message')

            tag = 'infoleak:automatic-detection="certificate"'
            self.add_message_to_queue(message=tag, queue='Tags')
            # find = True

        if KeyEnum.RSA_PRIVATE_KEY.value in content:
            print(f'{self.obj.get_global_id()} has a RSA private key message')
            print('rsa private key message found')

            tag = 'infoleak:automatic-detection="rsa-private-key"'
            self.add_message_to_queue(message=tag, queue='Tags')
            # find = True

        if KeyEnum.PRIVATE_KEY.value in content:
            print(f'{self.obj.get_global_id()} has a private key message')
            print('private key message found')

            tag = 'infoleak:automatic-detection="private-key"'
            self.add_message_to_queue(message=tag, queue='Tags')
            # find = True

        if KeyEnum.ENCRYPTED_PRIVATE_KEY.value in content:
            print(f'{self.obj.get_global_id()} has an encrypted private key message')
            print('encrypted private key message found')

            tag = 'infoleak:automatic-detection="encrypted-private-key"'
            self.add_message_to_queue(message=tag, queue='Tags')
            # find = True

        if KeyEnum.OPENSSH_PRIVATE_KEY.value in content:
            print(f'{self.obj.get_global_id()} has an openssh private key message')
            print('openssh private key message found')

            tag = 'infoleak:automatic-detection="private-ssh-key"'
            self.add_message_to_queue(message=tag, queue='Tags')
            # find = True

        if KeyEnum.SSH2_ENCRYPTED_PRIVATE_KEY.value in content:
            print(f'{self.obj.get_global_id()} has an ssh2 private key message')
            print('SSH2 private key message found')

            tag = 'infoleak:automatic-detection="private-ssh-key"'
            self.add_message_to_queue(message=tag, queue='Tags')
            # find = True

        if KeyEnum.OPENVPN_STATIC_KEY_V1.value in content:
            print(f'{self.obj.get_global_id()} has an openssh private key message')
            print('OpenVPN Static key message found')

            tag = 'infoleak:automatic-detection="vpn-static-key"'
            self.add_message_to_queue(message=tag, queue='Tags')
            # find = True

        if KeyEnum.DSA_PRIVATE_KEY.value in content:
            print(f'{self.obj.get_global_id()} has a dsa private key message')

            tag = 'infoleak:automatic-detection="dsa-private-key"'
            self.add_message_to_queue(message=tag, queue='Tags')
            # find = True

        if KeyEnum.EC_PRIVATE_KEY.value in content:
            print(f'{self.obj.get_global_id()} has an ec private key message')

            tag = 'infoleak:automatic-detection="ec-private-key"'
            self.add_message_to_queue(message=tag, queue='Tags')
            # find = True

        if KeyEnum.PUBLIC_KEY.value in content:
            print(f'{self.obj.get_global_id()} has a public key message')

            tag = 'infoleak:automatic-detection="public-key"'
            self.add_message_to_queue(message=tag, queue='Tags')
            # find = True

        # pgp content
        if get_pgp_content:
            self.add_message_to_queue(queue='PgpDump')

        # if find :
        #     # Send to duplicate
        #     self.add_message_to_queue(item.get_id(), 'Duplicate')
        #     self.logger.debug(f'{item.get_id()} has key(s)')
        #     print(f'{item.get_id()} has key(s)')


if __name__ == '__main__':
    module = Keys()
    module.run()

#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import os
import sys

import zmq


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.abstract_importer import AbstractImporter
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader

class ZMQImporters(AbstractImporter):
    def __init__(self):
        super().__init__()
        self.subscribers = []
        # Initialize poll set
        self.poller = zmq.Poller()

    def add(self, address, channel):
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        r = subscriber.connect(address)
        print(r)
        subscriber.setsockopt_string(zmq.SUBSCRIBE, channel)
        self.subscribers.append(subscriber)

        self.poller.register(subscriber, zmq.POLLIN)

    def importer(self, timeout=None):  # -> FOR loop required
        """
        :param timeout: The timeout (in milliseconds) to wait for an event.
        If unspecified (or specified None), will wait forever for an event.
        :returns: messages generator
        """
        for event in self.poller.poll(timeout=timeout):
            socket, event_mask = event
            # DEBUG
            print(socket, event_mask)
            yield socket.recv()


class ZMQModuleImporter(AbstractModule):
    def __init__(self):
        super().__init__()

        config_loader = ConfigLoader()
        addresses = config_loader.get_config_str('ZMQ_Global', 'address')
        addresses = addresses.split(',')
        channel = config_loader.get_config_str('ZMQ_Global', 'channel')
        self.zmq_importer = ZMQImporters()
        for address in addresses:
            self.zmq_importer.add(address.strip(), channel)

    # TODO MESSAGE SOURCE - UI
    def get_message(self):
        for message in self.zmq_importer.importer():
            # remove channel from message
            yield message.split(b' ', 1)[1]

    def compute(self, messages):
        for message in messages:
            message = message.decode()
            print(message.split(' ', 1)[0])
            self.add_message_to_queue(message)


if __name__ == '__main__':
    module = ZMQModuleImporter()
    module.run()

#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

ZMQ Importer

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

from lib.objects.Items import Item

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
        self.default_feeder_name = config_loader.get_config_str("Module_Mixer", "default_unnamed_feed_name")

        addresses = config_loader.get_config_str('ZMQ_Global', 'address')
        addresses = addresses.split(',')
        channel = config_loader.get_config_str('ZMQ_Global', 'channel')
        self.zmq_importer = ZMQImporters()
        for address in addresses:
            self.zmq_importer.add(address.strip(), channel)

    def get_message(self):
        for message in self.zmq_importer.importer():
            # remove channel from message
            yield message.split(b' ', 1)[1]

    def compute(self, messages):
        for message in messages:
            message = message.decode()

            obj_id, gzip64encoded = message.split(' ', 1)  # TODO ADD LOGS
            splitted = obj_id.split('>>', 1)
            if len(splitted) == 2:
                feeder_name, obj_id = splitted
            else:
                feeder_name = self.default_feeder_name

            obj = Item(obj_id)
            # f'{source} {content}'
            relay_message = f'{feeder_name} {gzip64encoded}'

            print(f'feeder_name item::{obj_id}')
            self.add_message_to_queue(obj=obj, message=relay_message)


if __name__ == '__main__':
    module = ZMQModuleImporter()
    module.run()

#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

ZMQ Importer

"""
import os
import json
import sys
import zmq

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.abstract_importer import AbstractImporter
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import ail_files

from lib.objects.Items import Item

def get_zmq_filter():
    filters = {}
    file = os.path.join(os.environ['AIL_HOME'], 'files', 'zmq_filter')
    if not os.path.exists(file):
        return filters
    with open(file, 'r') as f:
        zmq_filter = f.read()
    zmq_filter = json.loads(zmq_filter)
    for d in zmq_filter:
        feeder_name = d.get('source')
        if not feeder_name:
            continue
        if feeder_name not in filters:
            filters[feeder_name] = []
        str_start = d.get('start')
        str_end = d.get('end')
        file_start = d.get('file_start')
        file_end = d.get('file_end')
        content = d.get('content')
        description = d.get('description')
        if not str_start and not str_end and not file_start and not file_end and not content:
            continue
        feeder = {'description': description}
        if str_start and str_end:
            feeder['start'] = str_start
            feeder['end'] = str_end
        if file_start:
            feeder['file_start'] = file_start
        if file_end:
            feeder['file_end'] = file_end
        if content:
            feeder['content'] = content
        filters[feeder_name].append(feeder)
    print('loaded zmq filters: ', filters)
    return filters

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
            # print(socket, event_mask)
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

        self.filters = get_zmq_filter()

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

            # Filters
            if feeder_name in self.filters:
                content = ail_files.get_b64_gzipped_content(gzip64encoded, 'ZMQImporter')
                if content:
                    content = content.decode()

                    # TODO remove empty line ???
                    to_filter = False
                    for f in self.filters[feeder_name]:
                        if 'start' and 'end' in f:
                            if content.startswith(f['start']) and content.endswith(f['end']):
                                same_pattern = True
                                for line in content.splitlines():
                                    if line:
                                        if not (line.startswith(f['start']) and line.endswith(f['end'])):
                                            same_pattern = False
                                            break
                                if same_pattern:
                                    to_filter = True
                                    filter_description = f['description']
                                    break
                        elif 'content' in f:
                            if content == f['content']:
                                to_filter = True
                                filter_description = f['description']
                                break
                        elif 'file_start' in f:
                            if content.startswith(f['file_start']):
                                to_filter = True
                                filter_description = f['description']
                                break
                        elif 'file_end' in f:
                            if content.endswith(f['file_end']):
                                to_filter = True
                                filter_description = f['description']
                                break

                    # Filter content
                    if to_filter:
                        print(f'Filtered -------- {feeder_name}: {obj_id} -------- {filter_description}')
                        continue

            obj = Item(obj_id)
            # f'{source} {content}'
            relay_message = f'{feeder_name} {gzip64encoded}'

            print(f'{feeder_name} item::{obj_id}')
            self.add_message_to_queue(obj=obj, message=relay_message)


if __name__ == '__main__':
    module = ZMQModuleImporter()
    module.run()

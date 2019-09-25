#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Tools Module
============================

Search tools outpout

"""

from Helper import Process
from pubsublogger import publisher

import os
import re
import sys
import time
import redis
import signal

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item


class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)


def search_tools(item_id, item_content):

    tools_in_item = False

    for tools_name in tools_dict:
        tool_dict = tools_dict[tools_name]

        regex_match = False
        for regex_nb in list(range(tool_dict['nb_regex'])):
            regex_index = tool_dict['nb_regex'] + 1
            regex = tools_dict['regex{}'.format(regex_index)]

            signal.alarm(crypto_dict['max_execution_time'])
            try:
                tools_found = re.findall(regex, item_content)
            except TimeoutException:
                tools_found = []
                p.incr_module_timeout_statistic() # add encoder type
                print ("{0} processing timeout".format(item_id))
                continue
            else:
                signal.alarm(0)


            if not tools_found:
                regex_match = False
                break
            else:
                regex_match = True
                if 'tag{}'.format(regex_index) in tool_dict:
                    msg = '{};{}'.format(tool_dict['tag{}'.format(regex_index)], item_id)
                    p.populate_set_out(msg, 'Tags')

        if tools_found:
            # Tag Item
            msg = '{};{}'.format(tool_dict['tag'], item_id)
            p.populate_set_out(msg, 'Tags')


    if tools_in_item:
        # send to duplicate module
        p.populate_set_out(item_id, 'Duplicate')


default_max_execution_time = 30

tools_dict = {
    'tools_name': {
                    'name': 'tools_name',
                    'regex1': r'tools-regex1',
                    'tag1': 'tag to add if we found something with the regex1',
                    'regex2': r'tools-regex2',
                    'nb_regex': 2,
                    'max_execution_time': default_max_execution_time,
                    'tag': 'infoleak:automatic-detection="tools-name"', # tag if all regex match
    },
}


if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Bitcoin'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Run Tools module ")

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        item_id = p.get_from_set()
        if item_id is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        item_content = Item.get_item_content(item_id)
        search_tools(item_id, item_content)

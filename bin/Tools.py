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
            regex_index = regex_nb + 1
            regex = tool_dict['regex{}'.format(regex_index)]

            signal.alarm(tool_dict['max_execution_time'])
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
                    print('{} found: {}'.format(item_id, tool_dict['tag{}'.format(regex_index)]))
                    msg = '{};{}'.format(tool_dict['tag{}'.format(regex_index)], item_id)
                    p.populate_set_out(msg, 'Tags')

        if regex_match:
            print('{} found: {}'.format(item_id, tool_dict['name']))
            # Tag Item
            msg = '{};{}'.format(tool_dict['tag'], item_id)
            p.populate_set_out(msg, 'Tags')


    if tools_in_item:
        # send to duplicate module
        p.populate_set_out(item_id, 'Duplicate')


default_max_execution_time = 30

tools_dict = {
    'sqlmap': {
        'name': 'sqlmap',
        'regex1': r'Usage of sqlmap for attacking targets without|all tested parameters do not appear to be injectable|sqlmap identified the following injection point|Title:[^\n]*((error|time|boolean)-based|stacked queries|UNION query)',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="sqlmap-tool"', # tag if all regex match
    },
    'wig': {
        'name': 'wig',
        'regex1': r'(?s)wig - WebApp Information Gatherer.+?_{10,}',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="wig-tool"', # tag if all regex match
    },
    'dmytry': {
        'name': 'dmitry',
        'regex1': r'(?s)Gathered (TCP Port|Inet-whois|Netcraft|Subdomain|E-Mail) information for.+?-{10,}',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dmitry-tool"', # tag if all regex match
    },
    'inurlbr': {
        'name': 'inurlbr',
        'regex1': r'Usage of INURLBR for attacking targets without prior mutual consent is illegal',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="inurlbr-tool"', # tag if all regex match
    },
    'wafw00f': {
        'name': 'wafw00f',
        'regex1': r'(?s)WAFW00F - Web Application Firewall Detection Tool.+?Checking',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="wafw00f-tool"', # tag if all regex match
    },
    'sslyze': {
        'name': 'sslyze',
        'regex1': r'(?s)PluginSessionRenegotiation.+?SCAN RESULTS FOR',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="sslyze-tool"', # tag if all regex match
    },
    'nmap': {
        'name': 'nmap',
        'regex1': r'(?s)Nmap scan report for.+?Host is',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="nmap-tool"', # tag if all regex match
    },
    'dnsenum': {
        'name': 'dnsenum',
        'regex1': r'(?s)dnsenum VERSION:.+?Trying Zone Transfer',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dnsenum-tool"', # tag if all regex match
    },
    'knock': {
        'name': 'knock',
        'regex1': r'I scannig with my internal wordlist',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="knock-tool"', # tag if all regex match
    },
    'nikto': {
        'name': 'nikto',
        'regex1': r'(?s)\+ Target IP:.+?\+ Start Time:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="nikto-tool"', # tag if all regex match
    },
    'dnscan': {
        'name': 'dnscan',
        'regex1': r'(?s)\[\*\] Processing domain.+?\[\+\] Getting nameservers.+?records found',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dnscan-tool"', # tag if all regex match
    },
    'dnsrecon': {
        'name': 'dnsrecon',
        'regex1': r'Performing General Enumeration of Domain:|Performing TLD Brute force Enumeration against',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dnsrecon-tool"', # tag if all regex match
    },
    'striker': {
        'name': 'striker',
        'regex1': r'Crawling the target for fuzzable URLs|Honeypot Probabilty:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="striker-tool"', # tag if all regex match
    },
    'rhawk': {
        'name': 'rhawk',
        'regex1': r'S U B - D O M A I N   F I N D E R',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="rhawk-tool"', # tag if all regex match
    },
    'uniscan': {
        'name': 'uniscan',
        'regex1': r'\| \[\+\] E-mail Found:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="uniscan-tool"', # tag if all regex match
    },
}


if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Tools'
    # # TODO: add duplicate

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Run Tools module ")

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        item_id = p.get_from_set()
        item_id = 'submitted/2019/09/25/4c299ce1-0147-4727-8030-d77f903a9774.gz'
        if item_id is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        item_content = Item.get_item_content(item_id)
        search_tools(item_id, item_content)

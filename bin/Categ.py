#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The ZMQ_PubSub_Categ Module
============================

This module is consuming the Redis-list created by the ZMQ_PubSub_Tokenize_Q
Module.

Each words files created under /files/ are representing categories.
This modules take these files and compare them to
the stream of data given by the ZMQ_PubSub_Tokenize_Q  Module.

When a word from a paste match one or more of these words file, the filename of
the paste is published/forwarded to the next modules.

Each category (each files) are representing a dynamic channel.
This mean that if you create 1000 files under /files/ you'll have 1000 channels
where every time there is a matching word to a category, the paste containing
this word will be pushed to this specific channel.

..note:: The channel will have the name of the file created.

Implementing modules can start here, create your own category file,
and then create your own module to treat the specific paste matching this
category.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances. (Redis)
*Categories files of words in /files/ need to be created
*Need the ZMQ_PubSub_Tokenize_Q Module running to be able to work properly.

"""
import os
import argparse
import time
import re
from pubsublogger import publisher
from packages import Paste

from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Categ'

    p = Process(config_section)
    matchingThreshold = p.config.getint("Categ", "matchingThreshold")

    # SCRIPT PARSER #
    parser = argparse.ArgumentParser(description='Start Categ module on files.')

    parser.add_argument(
        '-d', type=str, default="../files/",
        help='Path to the directory containing the category files.',
        action='store')

    args = parser.parse_args()

    # FUNCTIONS #
    publisher.info("Script Categ started")

    categories = ['CreditCards', 'Mail', 'Onion', 'Web', 'Credential', 'Cve', 'ApiKey']
    tmp_dict = {}
    for filename in categories:
        bname = os.path.basename(filename)
        tmp_dict[bname] = []
        with open(os.path.join(args.d, filename), 'r') as f:
            patterns = [r'%s' % ( re.escape(s.strip()) ) for s in f]
            tmp_dict[bname] = re.compile('|'.join(patterns), re.IGNORECASE)

    prec_filename = None

    while True:
        filename = p.get_from_set()
        if filename is None:
            publisher.debug("Script Categ is Idling 10s")
            print('Sleeping')
            time.sleep(10)
            continue

        paste = Paste.Paste(filename)
        content = paste.get_p_content()

        for categ, pattern in tmp_dict.items():
            found = set(re.findall(pattern, content))
            if len(found) >= matchingThreshold:
                msg = '{} {}'.format(paste.p_rel_path, len(found))

                print(msg, categ)
                p.populate_set_out(msg, categ)

                publisher.info(
                    'Categ;{};{};{};Detected {} as {};{}'.format(
                        paste.p_source, paste.p_date, paste.p_name,
                        len(found), categ, paste.p_rel_path))

#!/usr/bin/env python2
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
import glob
import os
import argparse
import time
from pubsublogger import publisher
from packages import Paste

import Helper

if __name__ == "__main__":
    publisher.channel = "Script"

    config_section = 'PubSub_Words'
    config_channel = 'channel_0'
    subscriber_name = 'pubcateg'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    # Publisher
    pub_config_section = 'PubSub_Categ'

    h.zmq_pub(pub_config_section, None)

    # SCRIPT PARSER #
    parser = argparse.ArgumentParser(
        description='This script is a part of the Analysis Information \
                    Leak framework.')

    parser.add_argument(
        '-d', type=str, default="../files/",
        help='Path to the directory containing the category files.',
        action='store')

    args = parser.parse_args()

    # FUNCTIONS #
    publisher.info(
        "Script Categ subscribed to channel {}".format(h.sub_channel))

    tmp_dict = {}
    for filename in glob.glob(args.d):
        bname = os.path.basename(filename)
        tmp_dict[bname] = []
        with open(filename, 'r') as f:
            for l in f:
                tmp_dict[bname].append(l.strip())

    prec_filename = None

    while True:
        message = h.redis_rpop()
        if message is not None:
            channel, filename, word, score = message.split()

            if prec_filename is None or filename != prec_filename:
                PST = Paste.Paste(filename)
                prec_filename = filename

            for categ, words_list in tmp_dict.items():

                if word.lower() in words_list:
                    h.pub_channel = categ
                    h.zmq_pub_send('{} {} {}'.format(PST.p_path, word, score))

                    publisher.info(
                        'Categ;{};{};{};Detected {} "{}"'.format(
                            PST.p_source, PST.p_date, PST.p_name, score, word))

        else:
            if h.redis_queue_shutdown():
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Script Categ is Idling 10s")
            time.sleep(10)

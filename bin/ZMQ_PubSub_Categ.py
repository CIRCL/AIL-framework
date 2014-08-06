#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_PubSub_Categ Module
============================

This module is consuming the Redis-list created by the ZMQ_PubSub_Tokenize_Q Module.

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
and then create your own module to treat the specific paste matching this category.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances. (Redis)
*Categories files of words in /files/ need to be created
*Need the ZMQ_PubSub_Tokenize_Q Module running to be able to work properly.

"""
import redis, argparse, zmq, ConfigParser, time
from packages import Paste as P
from packages import ZMQ_PubSub
from pubsublogger import publisher

configfile = './packages/config.cfg'

def main():
    """Main Function"""

    # CONFIG #
    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)

    # SCRIPT PARSER #
    parser = argparse.ArgumentParser(
    description = '''This script is a part of the Analysis Information
    Leak framework.''',
    epilog = '''''')

    parser.add_argument('-l',
    type = str,
    default = "../files/list_categ_files",
    help = 'Path to the list_categ_files (../files/list_categ_files)',
    action = 'store')

    args = parser.parse_args()

    # REDIS #
    r_serv = redis.StrictRedis(
        host = cfg.get("Redis_Queues", "host"),
        port = cfg.getint("Redis_Queues", "port"),
        db = cfg.getint("Redis_Queues", "db"))

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    channel = cfg.get("PubSub_Words", "channel_0")
    subscriber_name = "categ"
    subscriber_config_section = "PubSub_Words"

    publisher_name = "pubcateg"
    publisher_config_section = "PubSub_Categ"

    Sub = ZMQ_PubSub.ZMQSub(configfile, subscriber_config_section, channel, subscriber_name)
    Pub = ZMQ_PubSub.ZMQPub(configfile, publisher_config_section, publisher_name)

    # FUNCTIONS #
    publisher.info("Script Categ subscribed to channel {0}".format(cfg.get("PubSub_Words", "channel_0")))

    with open(args.l, 'rb') as L:
        tmp_dict = {}

        for num, fname in enumerate(L):
            #keywords temp list
            tmp_list = []

            with open(fname[:-1], 'rb') as LS:

                for num, kword in enumerate(LS):
                    tmp_list.append(kword[:-1])

                tmp_dict[fname.split('/')[-1][:-1]] = tmp_list

    paste_words = []
    message = Sub.get_msg_from_queue(r_serv)
    prec_filename = None

    while True:
        if message != None:
            channel, filename, word, score = message.split()

            if prec_filename == None or filename != prec_filename:
                PST = P.Paste(filename)

            prec_filename = filename

            for categ, list in tmp_dict.items():

                if word.lower() in list:
                    channel = categ
                    msg = channel+" "+PST.p_path+" "+word+" "+score
                    Pub.send_message(msg)
                    #dico_categ.add(categ)

                    publisher.info('{0};{1};{2};{3};{4}'.format("Categ", PST.p_source, PST.p_date, PST.p_name,"Detected "+score+" "+word))

        else:
            if r_serv.sismember("SHUTDOWN_FLAGS", "Categ"):
                r_serv.srem("SHUTDOWN_FLAGS", "Categ")
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Script Categ is Idling 10s")
            time.sleep(10)

        message = Sub.get_msg_from_queue(r_serv)


if __name__ == "__main__":
    main()

#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Sub_Curve Module
============================

This module is consuming the Redis-list created by the ZMQ_Sub_Curve_Q Module.

This modules update a .csv file used to draw curves representing selected words and their occurency per day.

..note:: The channel will have the name of the file created.

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
from packages import lib_words

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

    r_serv1 = redis.StrictRedis(
        host = cfg.get("Redis_Level_DB", "host"),
        port = cfg.get("Redis_Level_DB", "port"),
        db = 0)

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    channel = cfg.get("PubSub_Words", "channel_0")
    subscriber_name = "curve"
    subscriber_config_section = "PubSub_Words"

    Sub = ZMQ_PubSub.ZMQSub(configfile, subscriber_config_section, channel, subscriber_name)

    # FUNCTIONS #
    publisher.info("Script Curve subscribed to channel {0}".format(cfg.get("PubSub_Words", "channel_0")))

    paste_words = []
    message = Sub.get_msg_from_queue(r_serv)
    prec_filename = None
    while True:
        if message != None:
            channel, filename, word, score = message.split()
            if prec_filename == None or filename != prec_filename:
                PST = P.Paste(filename)
                lib_words.create_curve_with_word_file(r_serv1, "/home/user/AIL/var/www/static/csv/wordstrendingdata", "/home/user/AIL/files/wordfile", int(PST.p_date.year), int(PST.p_date.month))

            prec_filename = filename
            prev_score = r_serv1.hget(word.lower(), PST.p_date)
            print prev_score
            if prev_score != None:
                r_serv1.hset(word.lower(), PST.p_date, int(prev_score) + int(score))
            else:
                r_serv1.hset(word.lower(), PST.p_date, score)
             #r_serv.expire(word,86400) #1day

        else:
            if r_serv.sismember("SHUTDOWN_FLAGS", "Curve"):
                r_serv.srem("SHUTDOWN_FLAGS", "Curve")
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Script Curve is Idling")
            print "sleepin"
            time.sleep(1)

        message = Sub.get_msg_from_queue(r_serv)


if __name__ == "__main__":
    main()

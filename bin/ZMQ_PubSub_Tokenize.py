#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_PubSub_Lines Module
============================

This module is consuming the Redis-list created by the ZMQ_PubSub_Tokenize_Q Module.

It tokenize the content of the paste and publish the result in the following format:
    channel_name+' '+/path/of/the/paste.gz+' '+tokenized_word+' '+scoring

    ..seealso:: Paste method (_get_top_words)

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances. (Redis)
*Need the ZMQ_PubSub_Tokenize_Q Module running to be able to work properly.

"""
import redis
import ConfigParser
import time
from packages import Paste
from packages import ZMQ_PubSub
from pubsublogger import publisher

configfile = './packages/config.cfg'


def main():
    """Main Function"""

    # CONFIG #
    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)

    # REDIS #
    r_serv = redis.StrictRedis(
        host=cfg.get("Redis_Queues", "host"),
        port=cfg.getint("Redis_Queues", "port"),
        db=cfg.getint("Redis_Queues", "db"))

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    channel = cfg.get("PubSub_Longlines", "channel_1")
    subscriber_name = "tokenize"
    subscriber_config_section = "PubSub_Longlines"

    # Publisher
    publisher_config_section = "PubSub_Words"
    publisher_name = "pubtokenize"

    sub = ZMQ_PubSub.ZMQSub(configfile, subscriber_config_section, channel, subscriber_name)
    pub = ZMQ_PubSub.ZMQPub(configfile, publisher_config_section, publisher_name)

    channel_0 = cfg.get("PubSub_Words", "channel_0")

    # FUNCTIONS #
    publisher.info("Tokeniser subscribed to channel {0}".format(cfg.get("PubSub_Longlines", "channel_1")))

    while True:
        message = sub.get_msg_from_queue(r_serv)
        print message
        if message is not None:
            PST = Paste.Paste(message.split(" ", -1)[-1])
        else:
            if r_serv.sismember("SHUTDOWN_FLAGS", "Tokenize"):
                r_serv.srem("SHUTDOWN_FLAGS", "Tokenize")
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Tokeniser is idling 10s")
            time.sleep(10)
            print "sleepin"
            continue

        for word, score in PST._get_top_words().items():
            if len(word) >= 4:
                msg = channel_0+' '+PST.p_path+' '+str(word)+' '+str(score)
                pub.send_message(msg)
                print msg
            else:
                pass

if __name__ == "__main__":
    main()

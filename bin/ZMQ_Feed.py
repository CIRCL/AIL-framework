#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Feed_Q Module
=====================

This module is consuming the Redis-list created by the ZMQ_Feed_Q Module,
And save the paste on disk to allow others modules to work on them.

..todo:: Be able to choose to delete or not the saved paste after processing.
..todo:: Store the empty paste (unprocessed) somewhere in Redis.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances.
*Need the ZMQ_Feed_Q Module running to be able to work properly.

"""
import redis, zmq, ConfigParser, sys, base64, gzip, os, time
#import zlib
from pubsublogger import publisher
from packages import ZMQ_PubSub

configfile = './packages/config.cfg'

def main():
    """Main Function"""

    # CONFIG #
    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)

    #REDIS
    r_serv = redis.StrictRedis(
        host = cfg.get("Redis_Queues", "host"),
        port = cfg.getint("Redis_Queues", "port"),
        db = cfg.getint("Redis_Queues", "db"))

    # ZMQ #
    channel = cfg.get("Feed", "topicfilter")

    #Subscriber
    subscriber_name = "feed"
    subscriber_config_section = "Feed"
    #Publisher
    publisher_name = "pubfed"
    publisher_config_section = "PubSub_Global"

    Sub = ZMQ_PubSub.ZMQSub(configfile, subscriber_config_section, channel, subscriber_name)
    PubGlob = ZMQ_PubSub.ZMQPub(configfile, publisher_config_section, publisher_name)

    # LOGGING #
    publisher.channel = "Script"
    publisher.info("Feed Script started to receive & publish.")

    while True:

        message = Sub.get_msg_from_queue(r_serv)
        #Recovering the streamed message informations.
        if message != None:
            if len(message.split()) == 3:
                topic, paste, gzip64encoded = message.split()
                print paste
            else:
                #TODO Store the name of the empty paste inside a Redis-list.
                print "Empty Paste: not processed"
                publisher.debug("Empty Paste: {0} not processed".format(paste))
                continue
        else:
            if r_serv.sismember("SHUTDOWN_FLAGS", "Feed"):
                r_serv.srem("SHUTDOWN_FLAGS", "Feed")
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            print "Empty Queues: Waiting..."
            time.sleep(10)
            continue
        #Creating the full filepath
        filename = cfg.get("Directories", "pastes") + paste

        if not os.path.exists(filename.rsplit("/", 1)[0]):
            os.makedirs(filename.rsplit("/", 1)[0])
        else:
            #Path already existing
            pass

        decoded_gzip = base64.standard_b64decode(gzip64encoded)
        #paste, zlib.decompress(decoded_gzip, zlib.MAX_WBITS|16)

        with open(filename, 'wb') as F:
            F.write(decoded_gzip)

        msg = cfg.get("PubSub_Global", "channel")+" "+filename
        PubGlob.send_message(msg)
        publisher.debug("{0} Published".format(msg))


if __name__ == "__main__":
    main()

#!/usr/bin/env python2
# -*-coding:UTF-8 -*

"""
The ZMQ_Sub_Attribute Module
============================

This module is consuming the Redis-list created by the ZMQ_PubSub_Line_Q Module.

It perform a sorting on the line's length and publish/forward them to differents
channels:

*Channel 1 if max length(line) < max
*Channel 2 if max length(line) > max

The collected informations about the processed pastes
(number of lines and maximum length line) are stored in Redis.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances. (LevelDB & Redis)
*Need the ZMQ_PubSub_Line_Q Module running to be able to work properly.

"""
import redis, zmq, ConfigParser, time
from packages import Paste as P
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
        host = cfg.get("Redis_Data_Merging", "host"),
        port = cfg.getint("Redis_Data_Merging", "port"),
        db = cfg.getint("Redis_Data_Merging", "db"))

    r_serv1 = redis.StrictRedis(
        host = cfg.get("Redis_Queues", "host"),
        port = cfg.getint("Redis_Queues", "port"),
        db = cfg.getint("Redis_Queues", "db"))

    p_serv = r_serv.pipeline(False)

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    #Subscriber
    channel = cfg.get("PubSub_Global", "channel")
    subscriber_name = "attributes"
    subscriber_config_section = "PubSub_Global"

    Sub = ZMQ_PubSub.ZMQSub(configfile, subscriber_config_section, channel, subscriber_name)

    # FUNCTIONS #
    publisher.info("""ZMQ Attribute is Running""")

    while True:
	try:
            message = Sub.get_msg_from_queue(r_serv1)

            if message != None:
                PST = P.Paste(message.split(" ",-1)[-1])
            else:
                if r_serv1.sismember("SHUTDOWN_FLAGS", "Attributes"):
                    r_serv1.srem("SHUTDOWN_FLAGS", "Attributes")
                    print "Shutdown Flag Up: Terminating"
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                publisher.debug("Script Attribute is idling 10s")
                time.sleep(10)
                continue

            encoding = PST._get_p_encoding()
            language = PST._get_p_language()

            PST.save_attribute_redis(r_serv, "p_encoding", encoding)
            PST.save_attribute_redis(r_serv, "p_language", language)

            r_serv.sadd("Pastes_Objects",PST.p_path)

            PST.save_all_attributes_redis(r_serv)
        except IOError:
           print "CRC Checksum Failed on :", PST.p_path
           publisher.error('{0};{1};{2};{3};{4}'.format("Duplicate", PST.p_source, PST.p_date, PST.p_name, "CRC Checksum Failed" ))
           pass 


if __name__ == "__main__":
    main()

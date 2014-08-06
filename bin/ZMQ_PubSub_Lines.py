#!/usr/bin/env python2
# -*-coding:UTF-8 -*

"""
The ZMQ_PubSub_Lines Module
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

    parser.add_argument('-max',
    type = int,
    default = 500,
    help = 'The limit between "short lines" and "long lines" (500)',
    action = 'store')

    args = parser.parse_args()

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
    subscriber_name = "line"
    subscriber_config_section = "PubSub_Global"

    #Publisher
    publisher_config_section = "PubSub_Longlines"
    publisher_name = "publine"

    Sub = ZMQ_PubSub.ZMQSub(configfile, subscriber_config_section, channel, subscriber_name)

    Pub = ZMQ_PubSub.ZMQPub(configfile, publisher_config_section, publisher_name)

    channel_0 = cfg.get("PubSub_Longlines", "channel_0")
    channel_1 = cfg.get("PubSub_Longlines", "channel_1")

    # FUNCTIONS #
    publisher.info("""Lines script Subscribed to channel {0} and Start to publish
    on channel {1}, {2}""".format(cfg.get("PubSub_Global", "channel"),
    cfg.get("PubSub_Longlines", "channel_0"),
    cfg.get("PubSub_Longlines", "channel_1")))

    while True:
        try:
            message = Sub.get_msg_from_queue(r_serv1)
            if message != None:
                PST = P.Paste(message.split(" ",-1)[-1])
            else:
                if r_serv1.sismember("SHUTDOWN_FLAGS", "Lines"):
                    r_serv1.srem("SHUTDOWN_FLAGS", "Lines")
                    print "Shutdown Flag Up: Terminating"
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                publisher.debug("Tokeniser is idling 10s")
                time.sleep(10)
                continue

            lines_infos = PST.get_lines_info()

            PST.save_attribute_redis(r_serv, "p_nb_lines", lines_infos[0])
            PST.save_attribute_redis(r_serv, "p_max_length_line", lines_infos[1])

            r_serv.sadd("Pastes_Objects",PST.p_path)
            if lines_infos[1] >= args.max:
                msg = channel_0+" "+PST.p_path
            else:
                msg = channel_1+" "+PST.p_path

            Pub.send_message(msg)
        except IOError:
            print "CRC Checksum Error on : ", PST.p_path
            pass

if __name__ == "__main__":
    main()

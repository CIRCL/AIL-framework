#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Sub_Onion Module
============================

This module is consuming the Redis-list created by the ZMQ_Sub_Onion_Q Module.

It trying to extract url from paste and returning only ones which are tor related
(.onion)

    ..seealso:: Paste method (get_regex)

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances. (Redis)
*Need the ZMQ_Sub_Onion_Q Module running to be able to work properly.

"""
import redis, zmq, ConfigParser, json, pprint, time
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
        host = cfg.get("Redis_Queues", "host"),
        port = cfg.getint("Redis_Queues", "port"),
        db = cfg.getint("Redis_Queues", "db"))

    r_serv1 = redis.StrictRedis(
        host = cfg.get("Redis_Data_Merging", "host"),
        port = cfg.getint("Redis_Data_Merging", "port"),
        db = cfg.getint("Redis_Data_Merging", "db"))

    r_serv2 = redis.StrictRedis(
        host = cfg.get("Redis_Cache", "host"),
        port = cfg.getint("Redis_Cache", "port"),
        db = cfg.getint("Redis_Cache", "db"))


    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    Sub = ZMQ_PubSub.ZMQSub(configfile, "PubSub_Categ", "onion_categ", "tor")

    # FUNCTIONS #
    publisher.info("Script subscribed to channel onion_categ")


    #Getting the first message from redis.
    message = Sub.get_msg_from_queue(r_serv)
    prec_filename = None

    #Thanks to Faup project for this regex
    # https://github.com/stricaud/faup
    url_regex = "([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|onion|[a-zA-Z]{2}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*"

    while True:
        if message != None:
            channel, filename, word, score  = message.split()

            # "For each new paste"
            if prec_filename == None or filename != prec_filename:
                domains_list = []
                PST = P.Paste(filename)

                for x in PST.get_regex(url_regex):
                    #Extracting url with regex
                    credential, subdomain, domain, host, tld, port, resource_path, query_string, f1, f2, f3, f4 = x

                    if f1 == "onion":
                        domains_list.append(domain)

                #Saving the list of extracted onion domains.
                PST.__setattr__(channel, domains_list)
                PST.save_attribute_redis(r_serv1, channel, domains_list)
                pprint.pprint(domains_list)
                print PST.p_path
                if len(domains_list) > 0:
                    publisher.warning('{0};{1};{2};{3};{4}'.format("Onion", PST.p_source, PST.p_date, PST.p_name,"Detected " + str(len(domains_list))+" .onion(s)" ))
                else:
                    publisher.info('{0};{1};{2};{3};{4}'.format("Onion", PST.p_source, PST.p_date, PST.p_name, "Onion related" ))

            prec_filename = filename

        else:
            if r_serv.sismember("SHUTDOWN_FLAGS", "Onion"):
                r_serv.srem("SHUTDOWN_FLAGS", "Onion")
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Script url is Idling 10s")
            time.sleep(10)

        message = Sub.get_msg_from_queue(r_serv)


if __name__ == "__main__":
    main()

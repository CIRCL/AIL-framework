#!/usr/bin/env python
# -*-coding:UTF-8 -*
"""
The ZMQ_Feed_Q Module
=====================

This module is consuming the Redis-list created by the ZMQ_Feed_Q Module.

This module take all the feeds provided in the config.
Depending on the configuration, this module will process the feed as follow:
    operation_mode 1: "Avoid any duplicate from any sources"
        - The module maintain a list of content for each paste
            - If the content is new, process it
            - Else, do not process it but keep track for statistics on duplicate

    operation_mode 2: "Keep duplicate coming from different sources"
        - The module maintain a list of name given to the paste by the feeder
            - If the name has not yet been seen, process it
            - Elseif, the saved content associated with the paste is not the same, process it
            - Else, do not process it but keep track for statistics on duplicate

Note that the hash of the content is defined as the gzip64encoded

Requirements
------------

*Need running Redis instances.
*Need the ZMQ_Feed_Q Module running to be able to work properly.

"""
import base64
import os
import time
from pubsublogger import publisher
import redis
import ConfigParser

from Helper import Process


# CONFIG #
refresh_time = 30



if __name__ == '__main__':
    publisher.port = 6380
    publisher.channel = 'Script'

    config_section = 'Mixer'

    p = Process(config_section)

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)

    # REDIS #
    server = redis.StrictRedis(
        host=cfg.get("Redis_Mixer", "host"),
        port=cfg.getint("Redis_Mixer", "port"),
        db=cfg.getint("Redis_Mixer", "db"))

    # LOGGING #
    publisher.info("Feed Script started to receive & publish.")

    # OTHER CONFIG #
    operation_mode = cfg.getint("Module_Mixer", "operation_mode")
    ttl_key = cfg.getint("Module_Mixer", "ttl_duplicate")

    # STATS #
    processed_paste = 0
    processed_paste_per_feeder = {}
    duplicated_paste_per_feeder = {}
    time_1 = time.time()


    while True:

        message = p.get_from_set()
        if message is not None:
            splitted = message.split()
            if len(splitted) == 2:
                paste, gzip64encoded = splitted
                try:
                    feeder_name, paste_name = paste.split('>')
                    feeder_name.replace(" ","")
                except ValueError as e:
                    feeder_name = "unnamed_feeder"
                    paste_name = paste

                # Processed paste
                processed_paste += 1
                try:
                    processed_paste_per_feeder[feeder_name] += 1
                except KeyError as e:
                    # new feeder
                    processed_paste_per_feeder[feeder_name] = 1
                    duplicated_paste_per_feeder[feeder_name] = 0

                relay_message = "{0} {1}".format(paste_name, gzip64encoded)

                # Avoid any duplicate coming from any sources
                if operation_mode == 1:
                    if server.exists(gzip64encoded): # Content already exists
                        #STATS
                        duplicated_paste_per_feeder[feeder_name] += 1
                    else: # New content
                        p.populate_set_out(relay_message)
                    server.sadd(gzip64encoded, feeder_name)
                    server.expire(gzip64encoded, ttl_key)


                # Keep duplicate coming from different sources
                else:
                    # Filter to avoid duplicate 
                    content = server.get('HASH_'+paste_name)
                    if content is None:
                        # New content
                        # Store in redis for filtering
                        server.set('HASH_'+paste_name, content)
                        server.sadd(paste_name, feeder_name)
                        server.expire(paste_name, ttl_key)
                        server.expire('HASH_'+paste_name, ttl_key)
                        p.populate_set_out(relay_message)
                    else:
                        if gzip64encoded != content:
                            # Same paste name but different content
                            #STATS
                            duplicated_paste_per_feeder[feeder_name] += 1
                            server.sadd(paste_name, feeder_name)
                            server.expire(paste_name, ttl_key)
                            p.populate_set_out(relay_message)
                        else:
                            # Already processed
                            # Keep track of processed pastes
                            #STATS
                            duplicated_paste_per_feeder[feeder_name] += 1
                            continue

            else:
                # TODO Store the name of the empty paste inside a Redis-list.
                print "Empty Paste: not processed"
                publisher.debug("Empty Paste: {0} not processed".format(message))
        else:
            print "Empty Queues: Waiting..."
            if int(time.time() - time_1) > refresh_time:
                to_print = 'Mixer; ; ; ;mixer_all Processed {0} paste(s) in {1}sec'.format(processed_paste, refresh_time)
                print to_print
                publisher.info(to_print)
                processed_paste = 0

                for feeder, count in processed_paste_per_feeder.iteritems():
                    to_print = 'Mixer; ; ; ;mixer_{0} {0} Processed {1} paste(s) in {2}sec'.format(feeder, count, refresh_time)
                    print to_print
                    publisher.info(to_print)
                    processed_paste_per_feeder[feeder] = 0

                for feeder, count in duplicated_paste_per_feeder.iteritems():
                    to_print = 'Mixer; ; ; ;mixer_{0} {0} Duplicated {1} paste(s) in {2}sec'.format(feeder, count, refresh_time)
                    print to_print
                    publisher.info(to_print)
                    duplicated_paste_per_feeder[feeder] = 0

                time_1 = time.time()
            time.sleep(0.5)
            continue

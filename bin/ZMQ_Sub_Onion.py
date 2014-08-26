#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Sub_Onion Module
============================

This module is consuming the Redis-list created by the ZMQ_Sub_Onion_Q Module.

It trying to extract url from paste and returning only ones which are tor
related (.onion)

    ..seealso:: Paste method (get_regex)

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances. (Redis)
*Need the ZMQ_Sub_Onion_Q Module running to be able to work properly.

"""
import pprint
import time
from packages import Paste
from pubsublogger import publisher


import Helper

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'PubSub_Categ'
    config_channel = 'channel_2'
    subscriber_name = 'tor'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    # FUNCTIONS #
    publisher.info("Script subscribed to channel onion_categ")

    # Getting the first message from redis.
    message = h.redis_rpop()
    prec_filename = None

    # Thanks to Faup project for this regex
    # https://github.com/stricaud/faup
    url_regex = "([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|onion|[a-zA-Z]{2}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*"

    while True:
        if message is not None:
            channel, filename, word, score = message.split()

            # "For each new paste"
            if prec_filename is None or filename != prec_filename:
                domains_list = []
                PST = Paste.Paste(filename)

                for x in PST.get_regex(url_regex):
                    # Extracting url with regex
                    credential, subdomain, domain, host, tld, port, \
                        resource_path, query_string, f1, f2, f3, f4 = x

                    if f1 == "onion":
                        domains_list.append(domain)

                # Saving the list of extracted onion domains.
                PST.__setattr__(channel, domains_list)
                PST.save_attribute_redis(channel, domains_list)
                pprint.pprint(domains_list)
                print PST.p_path
                to_print = 'Onion;{};{};{};'.format(PST.p_source, PST.p_date,
                                                    PST.p_name)
                if len(domains_list) > 0:
                    publisher.warning('{}Detected {} .onion(s)'.format(
                        to_print, len(domains_list)))
                else:
                    publisher.info('{}Onion related'.format(to_print))

            prec_filename = filename

        else:
            if h.redis_queue_shutdown():
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Script url is Idling 10s")
            time.sleep(10)

        message = h.redis_rpop()

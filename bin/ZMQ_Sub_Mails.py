#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis
import pprint
import time
import dns.exception
from packages import Paste
from packages import lib_refine
from pubsublogger import publisher

import Helper

if __name__ == "__main__":
    publisher.channel = "Script"

    config_section = 'PubSub_Categ'
    config_channel = 'channel_1'
    subscriber_name = 'emails'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    # Subscriber
    h.zmq_sub(config_section)

    # REDIS #
    r_serv2 = redis.StrictRedis(
        host=h.config.get("Redis_Cache", "host"),
        port=h.config.getint("Redis_Cache", "port"),
        db=h.config.getint("Redis_Cache", "db"))

    # FUNCTIONS #
    publisher.info("Suscribed to channel mails_categ")

    message = h.redis_rpop()
    prec_filename = None

    # Log as critical if there are more that that amout of valid emails
    is_critical = 10

    email_regex = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}"

    while True:
        try:
            if message is not None:
                channel, filename, word, score = message.split()

                if prec_filename is None or filename != prec_filename:
                    PST = Paste.Paste(filename)
                    MX_values = lib_refine.checking_MX_record(
                        r_serv2, PST.get_regex(email_regex))

                    if MX_values[0] >= 1:

                        PST.__setattr__(channel, MX_values)
                        PST.save_attribute_redis(channel, (MX_values[0],
                                                 list(MX_values[1])))

                        pprint.pprint(MX_values)
                        to_print = 'Mails;{};{};{};Checked {} e-mail(s)'.\
                            format(PST.p_source, PST.p_date, PST.p_name,
                                   MX_values[0])
                        if MX_values[0] > is_critical:
                            publisher.warning(to_print)
                        else:
                            publisher.info(to_print)
                prec_filename = filename

            else:
                if h.redis_queue_shutdown():
                    print "Shutdown Flag Up: Terminating"
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                publisher.debug("Script Mails is Idling 10s")
                time.sleep(10)

            message = h.redis_rpop()
        except dns.exception.Timeout:
            # FIXME retry!
            print "dns.exception.Timeout"

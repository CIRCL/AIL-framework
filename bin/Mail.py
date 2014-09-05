#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis
import pprint
import time
import dns.exception
from packages import Paste
from packages import lib_refine
from pubsublogger import publisher

from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Mail'

    p = Process(config_section)

    # REDIS #
    r_serv2 = redis.StrictRedis(
        host=p.config.get("Redis_Cache", "host"),
        port=p.config.getint("Redis_Cache", "port"),
        db=p.config.getint("Redis_Cache", "db"))

    # FUNCTIONS #
    publisher.info("Suscribed to channel mails_categ")

    # FIXME For retro compatibility
    channel = 'mails_categ'

    message = p.get_from_set()
    prec_filename = None

    # Log as critical if there are more that that amout of valid emails
    is_critical = 10

    email_regex = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}"
    MX_values = None
    while True:
        if message is not None:
            filename, score = message.split()

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
            publisher.debug("Script Mails is Idling 10s")
            print 'Sleeping'
            time.sleep(10)

        message = p.get_from_set()

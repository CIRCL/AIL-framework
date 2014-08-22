#!/usr/bin/env python2
# -*-coding:UTF-8 -*
import pprint
import time
from packages import Paste
from packages import lib_refine
from pubsublogger import publisher

import Helper

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'PubSub_Categ'
    config_channel = 'channel_0'
    subscriber_name = 'cards'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    # Subscriber
    h.zmq_sub(config_section)

    # FUNCTIONS #
    publisher.info("Creditcard script subscribed to channel creditcard_categ")

    message = h.redis_rpop()
    prec_filename = None

    creditcard_regex = "4[0-9]{12}(?:[0-9]{3})?"

    # mastercard_regex = "5[1-5]\d{2}([\ \-]?)\d{4}\1\d{4}\1\d{4}"
    # visa_regex = "4\d{3}([\ \-]?)\d{4}\1\d{4}\1\d{4}"
    # discover_regex = "6(?:011\d\d|5\d{4}|4[4-9]\d{3}|22(?:1(?:2[6-9]|
    #                   [3-9]\d)|[2-8]\d\d|9(?:[01]\d|2[0-5])))\d{10}"
    # jcb_regex = "35(?:2[89]|[3-8]\d)([\ \-]?)\d{4}\1\d{4}\1\d{4}"
    # amex_regex = "3[47]\d\d([\ \-]?)\d{6}\1\d{5}"
    # chinaUP_regex = "62[0-5]\d{13,16}"
    # maestro_regex = "(?:5[0678]\d\d|6304|6390|67\d\d)\d{8,15}"

    while True:
        if message is not None:
            channel, filename, word, score = message.split()

            if prec_filename is None or filename != prec_filename:
                creditcard_set = set([])
                PST = Paste.Paste(filename)

                for x in PST.get_regex(creditcard_regex):
                    if lib_refine.is_luhn_valid(x):
                        creditcard_set.add(x)

                PST.__setattr__(channel, creditcard_set)
                PST.save_attribute_redis(channel, creditcard_set)

                pprint.pprint(creditcard_set)
                to_print = 'CreditCard;{};{};{};'.format(
                    PST.p_source, PST.p_date, PST.p_name)
                if (len(creditcard_set) > 0):
                    publisher.critical('{}Checked {} valid number(s)'.format(
                        to_print, len(creditcard_set)))
                else:
                    publisher.info('{}CreditCard related'.format(to_print))

            prec_filename = filename

        else:
            if h.redis_queue_shutdown():
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Script creditcard is idling 1m")
            time.sleep(60)

        message = h.redis_rpop()

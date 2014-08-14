#!/usr/bin/env python2
# -*-coding:UTF-8 -*
import redis
import ConfigParser
import pprint
import time
from packages import Paste
from packages import lib_refine
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

    r_serv1 = redis.StrictRedis(
        host=cfg.get("Redis_Data_Merging", "host"),
        port=cfg.getint("Redis_Data_Merging", "port"),
        db=cfg.getint("Redis_Data_Merging", "db"))

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    sub = ZMQ_PubSub.ZMQSub(configfile, "PubSub_Categ", "creditcard_categ", "cards")

    # FUNCTIONS #
    publisher.info("Creditcard script subscribed to channel creditcard_categ")

    message = sub.get_msg_from_queue(r_serv)
    prec_filename = None

    creditcard_regex = "4[0-9]{12}(?:[0-9]{3})?"

    # mastercard_regex = "5[1-5]\d{2}([\ \-]?)\d{4}\1\d{4}\1\d{4}"
    # visa_regex = "4\d{3}([\ \-]?)\d{4}\1\d{4}\1\d{4}"
    # discover_regex = "6(?:011\d\d|5\d{4}|4[4-9]\d{3}|22(?:1(?:2[6-9]|[3-9]\d)|[2-8]\d\d|9(?:[01]\d|2[0-5])))\d{10}"
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
                PST.save_attribute_redis(r_serv1, channel, creditcard_set)

                pprint.pprint(creditcard_set)
                to_print = 'CreditCard;{};{};{};'.format(PST.p_source, PST.p_date, PST.p_name)
                if (len(creditcard_set) > 0):
                    publisher.critical('{}Checked {} valid number(s)'.format(to_print, len(creditcard_set)))
                else:
                    publisher.info('{}CreditCard related'.format(to_print))

            prec_filename = filename

        else:
            if r_serv.sismember("SHUTDOWN_FLAGS", "Creditcards"):
                r_serv.srem("SHUTDOWN_FLAGS", "Creditcards")
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Script creditcard is idling 1m")
            time.sleep(60)

        message = sub.get_msg_from_queue(r_serv)


if __name__ == "__main__":
    main()

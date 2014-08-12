#!/usr/bin/env python2
# -*-coding:UTF-8 -*
import redis, zmq, ConfigParser, json, pprint, time
from packages import Paste as P
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
        host = cfg.get("Redis_Queues", "host"),
        port = cfg.getint("Redis_Queues", "port"),
        db = cfg.getint("Redis_Queues", "db"))

    r_serv1 = redis.StrictRedis(
        host = cfg.get("Redis_Data_Merging", "host"),
        port = cfg.getint("Redis_Data_Merging", "port"),
        db = cfg.getint("Redis_Data_Merging", "db"))

    p_serv = r_serv.pipeline(False)

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    Sub = ZMQ_PubSub.ZMQSub(configfile, "PubSub_Categ", "creditcard_categ", "cards")

    # FUNCTIONS #
    publisher.info("Creditcard script subscribed to channel creditcard_categ")

    message = Sub.get_msg_from_queue(r_serv)
    prec_filename = None

    creditcard_regex = "4[0-9]{12}(?:[0-9]{3})?"

    mastercard_regex = "5[1-5]\d{2}([\ \-]?)\d{4}\1\d{4}\1\d{4}"
    visa_regex = "4\d{3}([\ \-]?)\d{4}\1\d{4}\1\d{4}"
    discover_regex = "6(?:011\d\d|5\d{4}|4[4-9]\d{3}|22(?:1(?:2[6-9]|[3-9]\d)|[2-8]\d\d|9(?:[01]\d|2[0-5])))\d{10}"
    jcb_regex = "35(?:2[89]|[3-8]\d)([\ \-]?)\d{4}\1\d{4}\1\d{4}"
    amex_regex = "3[47]\d\d([\ \-]?)\d{6}\1\d{5}"
    chinaUP_regex = "62[0-5]\d{13,16}"
    maestro_regex = "(?:5[0678]\d\d|6304|6390|67\d\d)\d{8,15}"

    while True:
        if message != None:
            channel, filename, word, score  = message.split()

            if prec_filename == None or filename != prec_filename:
                Creditcard_set = set([])
                PST = P.Paste(filename)

                for x in PST.get_regex(creditcard_regex):
                    if lib_refine.is_luhn_valid(x):
                        Creditcard_set.add(x)


                PST.__setattr__(channel, Creditcard_set)
                PST.save_attribute_redis(r_serv1, channel, Creditcard_set)

                pprint.pprint(Creditcard_set)
                if (len(Creditcard_set) > 0):
                    publisher.critical('{0};{1};{2};{3};{4}'.format("CreditCard", PST.p_source, PST.p_date, PST.p_name,"Checked " + str(len(Creditcard_set))+" valid number(s)" ))
                else:
                    publisher.info('{0};{1};{2};{3};{4}'.format("CreditCard", PST.p_source, PST.p_date, PST.p_name, "CreditCard related" ))

            prec_filename = filename

        else:
            if r_serv.sismember("SHUTDOWN_FLAGS", "Creditcards"):
                r_serv.srem("SHUTDOWN_FLAGS", "Creditcards")
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            publisher.debug("Script creditcard is idling 1m")
            time.sleep(60)

        message = Sub.get_msg_from_queue(r_serv)


if __name__ == "__main__":
    main()

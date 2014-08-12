#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import redis, zmq, ConfigParser, json, pprint, time
import dns.exception
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

    r_serv2 = redis.StrictRedis(
        host = cfg.get("Redis_Cache", "host"),
        port = cfg.getint("Redis_Cache", "port"),
        db = cfg.getint("Redis_Cache", "db"))

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    Sub = ZMQ_PubSub.ZMQSub(configfile,"PubSub_Categ", "mails_categ", "emails")

    # FUNCTIONS #
    publisher.info("Suscribed to channel mails_categ")

    message = Sub.get_msg_from_queue(r_serv)
    prec_filename = None

    email_regex = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}"

    while True:
        try:
            if message != None:
                channel, filename, word, score  = message.split()

                if prec_filename == None or filename != prec_filename:
                    PST = P.Paste(filename)
                    MX_values = lib_refine.checking_MX_record(r_serv2, PST.get_regex(email_regex))

                    if MX_values[0] >= 1:

                        PST.__setattr__(channel, MX_values)
                        PST.save_attribute_redis(r_serv1, channel, (MX_values[0], list(MX_values[1])))

                        pprint.pprint(MX_values)
                        if MX_values[0] > 10:
                            publisher.warning('{0};{1};{2};{3};{4}'.format("Mails", PST.p_source, PST.p_date, PST.p_name,"Checked "+ str(MX_values[0])+ " e-mails" ))
                        else:
                            publisher.info('{0};{1};{2};{3};{4}'.format("Mails", PST.p_source, PST.p_date, PST.p_name,"Checked " str(MX_values[0])+ " e-mail(s)" ))
                prec_filename = filename

            else:
                if r_serv.sismember("SHUTDOWN_FLAGS", "Mails"):
                    r_serv.srem("SHUTDOWN_FLAGS", "Mails")
                    print "Shutdown Flag Up: Terminating"
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                publisher.debug("Script Mails is Idling 10s")
                time.sleep(10)

            message = Sub.get_msg_from_queue(r_serv)
        except dns.exception.Timeout:
            print "dns.exception.Timeout"
            pass


if __name__ == "__main__":
    main()

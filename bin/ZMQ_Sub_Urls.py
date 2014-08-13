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
    #Subscriber
    subscriber_name = "urls"
    subscriber_config_section = "PubSub_Categ"

    #Publisher
    publisher_config_section = "PubSub_Url"
    publisher_name = "adress"
    pubchannel = cfg.get("PubSub_Url", "channel")

    Sub = ZMQ_PubSub.ZMQSub(configfile, subscriber_config_section, "web_categ", subscriber_name)
    Pub = ZMQ_PubSub.ZMQPub(configfile, publisher_config_section, publisher_name)

    #Sub = ZMQ_PubSub.ZMQSub(configfile, "PubSub_Categ", "web_categ", "urls")

    # FUNCTIONS #
    publisher.info("Script URL subscribed to channel web_categ")

    message = Sub.get_msg_from_queue(r_serv)
    prec_filename = None

    url_regex = "(http|https|ftp)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*"

    while True:
        try:
            if message != None:
                channel, filename, word, score  = message.split()

                if prec_filename == None or filename != prec_filename:
                    domains_list = []
                    PST = P.Paste(filename)

                    for x in PST.get_regex(url_regex):
                        scheme, credential, subdomain, domain, host, tld, port, resource_path, query_string, f1, f2, f3, f4 = x
                        domains_list.append(domain)
                        msg = pubchannel + " " + str(x)
                        Pub.send_message(msg)
                        publisher.debug('{0} Published'.format(x))

                        if f1 == "onion":
                            print domain

                    A_values = lib_refine.checking_A_record(r_serv2, domains_list)

                    if A_values[0] >= 1:
                        PST.__setattr__(channel, A_values)
                        PST.save_attribute_redis(r_serv1, channel, (A_values[0],list(A_values[1])))

                        pprint.pprint(A_values)
                        publisher.info('{0};{1};{2};{3};{4}'.format("Url", PST.p_source, PST.p_date, PST.p_name, "Checked " + str(A_values[0]) + " URL" ))
                prec_filename = filename

            else:
                if r_serv.sismember("SHUTDOWN_FLAGS", "Urls"):
                    r_serv.srem("SHUTDOWN_FLAGS", "Urls")
                    print "Shutdown Flag Up: Terminating"
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                publisher.debug("Script url is Idling 10s")
                time.sleep(10)

            message = Sub.get_msg_from_queue(r_serv)
        except dns.exception.Timeout:
            print "dns.exception.Timeout"
            pass

if __name__ == "__main__":
    main()

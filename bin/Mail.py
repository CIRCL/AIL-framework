#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Mail Module
======================

This module is consuming the Redis-list created by the Categ module.

It apply mail regexes on paste content and warn if above a threshold.

"""

import os
import sys
import redis
import time
import datetime
import dns.exception
from packages import Paste
from packages import lib_refine
from pubsublogger import publisher

from pyfaup.faup import Faup

from Helper import Process

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item

import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)
max_execution_time = 30

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Mail'

    faup = Faup()

    p = Process(config_section)
    addr_dns = p.config.get("Mail", "dns")

    # REDIS #
    r_serv_cache = redis.StrictRedis(
        host=p.config.get("Redis_Cache", "host"),
        port=p.config.getint("Redis_Cache", "port"),
        db=p.config.getint("Redis_Cache", "db"),
        decode_responses=True)
    # ARDB #
    server_statistics = redis.StrictRedis(
        host=p.config.get("ARDB_Statistics", "host"),
        port=p.config.getint("ARDB_Statistics", "port"),
        db=p.config.getint("ARDB_Statistics", "db"),
        decode_responses=True)

    # FUNCTIONS #
    publisher.info("Suscribed to channel mails_categ")

    # FIXME For retro compatibility
    channel = 'mails_categ'
    prec_item_id = None

    # Log as critical if there are more that that amout of valid emails
    is_critical = 10

    max_execution_time = 60
    email_regex = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}"
    MX_values = None
    while True:
        message = p.get_from_set()

        if message is not None:
            item_id, score = message.split()

            if prec_item_id is None or item_id != prec_item_id:
                PST = Paste.Paste(item_id)

                # max execution time on regex
                signal.alarm(max_execution_time)
                try:
                    l_mails = re.findall(email_regex, Item.get_item_content())
                except TimeoutException:
                    p.incr_module_timeout_statistic() # add encoder type
                    err_mess = "Mail: processing timeout: {}".format(item_id)
                    print(err_mess)
                    publisher.info(err_mess)
                    continue
                else:
                    signal.alarm(0)

                l_mails = list(set(l_mails))

                # max execution time on regex
                signal.alarm(max_execution_time)
                try:
                    # Transforming the set into a string
                    MXdomains = re.findall("@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,20}", str(l_mails).lower())
                except TimeoutException:
                    p.incr_module_timeout_statistic() # add encoder type
                    err_mess = "Mail: processing timeout: {}".format(item_id)
                    print(err_mess)
                    publisher.info(err_mess)
                    continue
                else:
                    signal.alarm(0)

                MX_values = lib_refine.checking_MX_record(r_serv_cache, MXdomains, addr_dns)

                if MX_values[0] >= 1:

                    PST.__setattr__(channel, MX_values)
                    PST.save_attribute_redis(channel, (MX_values[0],
                                             list(MX_values[1])))

                    to_print = 'Mails;{};{};{};Checked {} e-mail(s);{}'.\
                        format(PST.p_source, PST.p_date, PST.p_name,
                               MX_values[0], PST.p_rel_path)
                    if MX_values[0] > is_critical:
                        publisher.warning(to_print)
                        #Send to duplicate
                        p.populate_set_out(item_id, 'Duplicate')

                        msg = 'infoleak:automatic-detection="mail";{}'.format(item_id)
                        p.populate_set_out(msg, 'Tags')

                        #create country statistics
                        date = datetime.datetime.now().strftime("%Y%m")
                        for mail in MX_values[1]:
                            print('mail;{};{};{}'.format(MX_values[1][mail], mail, PST.p_date))
                            p.populate_set_out('mail;{};{};{}'.format(MX_values[1][mail], mail, PST.p_date), 'ModuleStats')

                            faup.decode(mail)
                            tld = faup.get()['tld']
                            try:
                                tld = tld.decode()
                            except:
                                pass
                            server_statistics.hincrby('mail_by_tld:'+date, tld, MX_values[1][mail])

                    else:
                        publisher.info(to_print)
                #create country statistics
                for mail in MX_values[1]:
                    print('mail;{};{};{}'.format(MX_values[1][mail], mail, PST.p_date))
                    p.populate_set_out('mail;{};{};{}'.format(MX_values[1][mail], mail, PST.p_date), 'ModuleStats')

            prec_item_id = item_id

        else:
            publisher.debug("Script Mails is Idling 10s")
            print('Sleeping')
            time.sleep(10)

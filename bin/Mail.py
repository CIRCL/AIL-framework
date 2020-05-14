#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Mails Module
======================

This module is consuming the Redis-list created by the Categ module.

It apply mail regexes on item content and warn if above a threshold.

"""

import os
import re
import sys
import uuid
import redis
import time
import datetime

import dns.resolver
import dns.exception

from multiprocessing import Process as Proc

from pubsublogger import publisher
from Helper import Process

from pyfaup.faup import Faup

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

## LOAD CONFIG ##
config_loader = ConfigLoader.ConfigLoader()
server_statistics = config_loader.get_redis_conn("ARDB_Statistics")
r_serv_cache = config_loader.get_redis_conn("Redis_Cache")

dns_server = config_loader.get_config_str('Mail', 'dns')

config_loader = None
## -- ##

def is_mxdomain_in_cache(mxdomain):
    return r_serv_cache.exists('mxdomain:{}'.format(mxdomain))

def save_mxdomain_in_cache(mxdomain):
    r_serv_cache.setex('mxdomain:{}'.format(mxdomain), 1, datetime.timedelta(days=1))

def check_mx_record(set_mxdomains, dns_server):
    """Check if emails MX domains are responding.

    :param adress_set: -- (set) This is a set of emails domains
    :return: (int) Number of adress with a responding and valid MX domains

    """
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    resolver.timeout = 5.0
    resolver.lifetime = 2.0

    valid_mxdomain = []
    for mxdomain in set_mxdomains:

        # check if is in cache
        # # TODO:
        if is_mxdomain_in_cache(mxdomain):
            valid_mxdomain.append(mxdomain)
        else:

            # DNS resolution
            try:
                answers = resolver.query(mxdomain, rdtype=dns.rdatatype.MX)
                if answers:
                    save_mxdomain_in_cache(mxdomain)
                    valid_mxdomain.append(mxdomain)
                    # DEBUG
                    # print('---')
                    # print(answers.response)
                    # print(answers.qname)
                    # print(answers.rdtype)
                    # print(answers.rdclass)
                    # print(answers.nameserver)
                    # print()

            except dns.resolver.NoNameservers:
                publisher.debug('NoNameserver, No non-broken nameservers are available to answer the query.')
                print('NoNameserver, No non-broken nameservers are available to answer the query.')
            except dns.resolver.NoAnswer:
                publisher.debug('NoAnswer, The response did not contain an answer to the question.')
                print('NoAnswer, The response did not contain an answer to the question.')
            except dns.name.EmptyLabel:
                publisher.debug('SyntaxError: EmptyLabel')
                print('SyntaxError: EmptyLabel')
            except dns.resolver.NXDOMAIN:
                #save_mxdomain_in_cache(mxdomain)
                publisher.debug('The query name does not exist.')
                print('The query name does not exist.')
            except dns.name.LabelTooLong:
                publisher.debug('The Label is too long')
                print('The Label is too long')
            except dns.exception.Timeout:
                print('dns timeout')
                #save_mxdomain_in_cache(mxdomain)
            except Exception as e:
                print(e)
    return valid_mxdomain

def extract_all_emails(redis_key, item_content):
    all_emails = re.findall(email_regex, item_content)
    if len(all_emails) > 1:
        r_serv_cache.sadd(redis_key, *all_emails)
        r_serv_cache.expire(redis_key, 360)
    elif all_emails:
        r_serv_cache.sadd(redis_key, all_emails[0])
        r_serv_cache.expire(redis_key, 360)

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Mail'

    faup = Faup()

    p = Process(config_section)

    publisher.info("Mails module started")

    # Numbers of Mails needed to Tags
    mail_threshold = 10

    max_execution_time = 30

    email_regex = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}"

    redis_key = 'mail_extracted:{}'.format(str(uuid.uuid4()))

    while True:
        message = p.get_from_set()

        if message is not None:
            item_id, score = message.split()

            print(item_id)

            item_content = Item.get_item_content(item_id)

            proc = Proc(target=extract_all_emails, args=(redis_key, item_content, ))
            try:
                proc.start()
                proc.join(max_execution_time)
                if proc.is_alive():
                    proc.terminate()
                    p.incr_module_timeout_statistic()
                    err_mess = "Mails: processing timeout: {}".format(item_id)
                    print(err_mess)
                    publisher.info(err_mess)
                    continue
                else:
                    all_emails = r_serv_cache.smembers(redis_key)
                    r_serv_cache.delete(redis_key)
                    proc.terminate()
            except KeyboardInterrupt:
                print("Caught KeyboardInterrupt, terminating workers")
                proc.terminate()
                sys.exit(0)

            # get MXdomains
            set_mxdomains = set()
            dict_mxdomains_email = {}
            for email in all_emails:
                mxdomain = email.split('@')[1].lower()
                if not mxdomain in dict_mxdomains_email:
                    dict_mxdomains_email[mxdomain] = []
                    set_mxdomains.add(mxdomain)
                dict_mxdomains_email[mxdomain].append(email)

                ## TODO: add MAIL trackers

            valid_mx = check_mx_record(set_mxdomains, dns_server)

            item_date = Item.get_item_date(item_id)

            num_valid_email = 0
            for domain_mx in valid_mx:
                num_valid_email += len(dict_mxdomains_email[domain_mx])

                for email in dict_mxdomains_email[domain_mx]:
                    msg = 'mail;{};{};{}'.format(1, email, item_date)
                    p.populate_set_out(msg, 'ModuleStats')

                    # Create country stats
                    faup.decode(email)
                    tld = faup.get()['tld']
                    try:
                        tld = tld.decode()
                    except:
                        pass
                    server_statistics.hincrby('mail_by_tld:{}'.format(item_date), tld, 1)

            msg = 'Mails;{};{};{};Checked {} e-mail(s);{}'.format(Item.get_source(item_id), item_date, Item.get_item_basename(item_id), num_valid_email, item_id)

            if num_valid_email > mail_threshold:
                print('{}    Checked {} e-mail(s)'.format(item_id, num_valid_email))
                publisher.warning(msg)
                #Send to duplicate
                p.populate_set_out(item_id, 'Duplicate')
                #tags
                msg = 'infoleak:automatic-detection="mail";{}'.format(item_id)
                p.populate_set_out(msg, 'Tags')
            else:
                publisher.info(msg)

        else:
            time.sleep(10)

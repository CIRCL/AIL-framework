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
import datetime

import dns.resolver
import dns.exception

# from pyfaup.faup import Faup

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages        #
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
# from lib import Statistics


class Mail(AbstractModule):
    """
    Module Mail module for AIL framework
    """

    def __init__(self, queue=True):
        super(Mail, self).__init__(queue=queue)

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")

        self.dns_server = config_loader.get_config_str('Mail', 'dns')

        # self.faup = Faup()

        # Numbers of Mails needed to Tags
        self.mail_threshold = 10

        self.regex_timeout = 30
        self.email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}"
        re.compile(self.email_regex)

    def is_mxdomain_in_cache(self, mxdomain):
        return self.r_cache.exists(f'mxdomain:{mxdomain}')

    def save_mxdomain_in_cache(self, mxdomain):
        self.r_cache.setex(f'mxdomain:{mxdomain}', datetime.timedelta(days=1), 1)

    def check_mx_record(self, set_mxdomains):
        """Check if emails MX domains are responding.

        :param set_mxdomains: -- (set) This is a set of emails domains
        :return: (int) Number of address with a responding and valid MX domains

        """
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [self.dns_server]
        resolver.timeout = 5.0
        resolver.lifetime = 2.0

        valid_mxdomain = []
        for mxdomain in set_mxdomains:

            # check if is in cache
            # # TODO:
            if self.is_mxdomain_in_cache(mxdomain):
                valid_mxdomain.append(mxdomain)
            else:

                # DNS resolution
                try:
                    answers = resolver.query(mxdomain, rdtype=dns.rdatatype.MX)
                    if answers:
                        self.save_mxdomain_in_cache(mxdomain)
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
                    self.logger.debug('NoNameserver, No non-broken nameservers are available to answer the query.')
                    print('NoNameserver, No non-broken nameservers are available to answer the query.')
                except dns.resolver.NoAnswer:
                    self.logger.debug('NoAnswer, The response did not contain an answer to the question.')
                    print('NoAnswer, The response did not contain an answer to the question.')
                except dns.name.EmptyLabel:
                    self.logger.debug('SyntaxError: EmptyLabel')
                    print('SyntaxError: EmptyLabel')
                except dns.resolver.NXDOMAIN:
                    # save_mxdomain_in_cache(mxdomain)
                    self.logger.debug('The query name does not exist.')
                    print('The query name does not exist.')
                except dns.name.LabelTooLong:
                    self.logger.debug('The Label is too long')
                    print('The Label is too long')
                except dns.exception.Timeout:
                    print('dns timeout')
                    # save_mxdomain_in_cache(mxdomain)
                except Exception as e:
                    print(e)
        return valid_mxdomain

    def extract(self, obj, content, tag, check_mx_record=False):
        extracted = []
        mxdomains = {}
        mails = self.regex_finditer(self.email_regex, obj.get_global_id(), content)
        for mail in mails:
            start, end, value = mail
            mxdomain = value.rsplit('@', 1)[1].lower()
            if mxdomain not in mxdomains:
                mxdomains[mxdomain] = []
            mxdomains[mxdomain].append(mail)
        if check_mx_record:
            for mx in self.check_mx_record(mxdomains.keys()):
                for row in mxdomains[mx]:
                    extracted.append([row[0], row[1], row[2], f'tag:{tag}'])
        else:
            for mx in mxdomains:
                for row in mxdomains[mx]:
                    extracted.append([row[0], row[1], row[2], f'tag:{tag}'])
        return extracted

    # # TODO: sanitize mails
    def compute(self, message):
        item = self.get_obj()

        mails = self.regex_findall(self.email_regex, item.id, item.get_content())
        mxdomains_email = {}
        for mail in mails:
            mxdomain = mail.rsplit('@', 1)[1].lower()
            if not mxdomain in mxdomains_email:
                mxdomains_email[mxdomain] = set()
            mxdomains_email[mxdomain].add(mail)

            # # TODO: add MAIL trackers

        valid_mx = self.check_mx_record(mxdomains_email.keys())
        print(f'valid_mx: {valid_mx}')
        # mx_tlds = {}
        num_valid_email = 0
        for domain_mx in valid_mx:
            nb_mails = len(mxdomains_email[domain_mx])
            num_valid_email += nb_mails

            # Create domain_mail stats
            # msg = f'mail;{nb_mails};{domain_mx};{item_date}'
            # self.add_message_to_queue(msg, 'ModuleStats')

            # Create country stats
            # self.faup.decode(domain_mx)
            # tld = self.faup.get()['tld']
            # try:
            #     tld = tld.decode()
            # except:
            #     pass
            # mx_tlds[tld] = mx_tlds.get(tld, 0) + nb_mails
        # for tld in mx_tlds:
        #     Statistics.add_module_tld_stats_by_date('mail', item_date, tld, mx_tlds[tld])

        msg = f'Checked {num_valid_email} e-mail(s);{self.obj.get_global_id()}'
        if num_valid_email > self.mail_threshold:
            print(f'{item.id}    Checked {num_valid_email} e-mail(s)')
            self.logger.info(msg)
            # Tags
            tag = 'infoleak:automatic-detection="mail"'
            self.add_message_to_queue(message=tag, queue='Tags')
        elif num_valid_email > 0:
            self.logger.info(msg)


if __name__ == '__main__':
    module = Mail()
    module.run()

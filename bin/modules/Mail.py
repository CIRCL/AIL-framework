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

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages        #
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib.objects import Mails
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

        # Numbers of Mails needed to Tags
        self.mail_threshold = 10

        self.regex_timeout = 30
        #self.email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}"
        self.email_regex = r"[\w._+-]+@[\w.-]+\.\w{2,63}"
        re.compile(self.email_regex)

        self.mail_correlation = {"domain", "item", "message"}
        # self.mail_item_banned_sources = {"alerts/gist.github.com", "archive/gist.github.com"}
        self.mail_item_allowed_sources = {"crawled", "submitted", "telegram"}

    def is_mxdomain_in_cache(self, mxdomain):
        return self.r_cache.exists(f'mxdomain:{mxdomain}')

    def is_mxdomain_in_cache_down(self, mxdomain):
        return self.r_cache.exists(f'mxdomain:down:{mxdomain}')

    def save_mxdomain_in_cache(self, mxdomain, is_up=True):
        if is_up:
            self.r_cache.setex(f'mxdomain:{mxdomain}', datetime.timedelta(days=1), 1)
        else:
            self.r_cache.setex(f'mxdomain:down:{mxdomain}', 3600, 0)

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
            # # TODO: SAVE INVALID IN CACHE ???
            if self.is_mxdomain_in_cache(mxdomain):
                valid_mxdomain.append(mxdomain)
            elif self.is_mxdomain_in_cache_down(mxdomain):
                print(f'cache down: {mxdomain}')
                continue
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
                    else:
                        self.save_mxdomain_in_cache(mxdomain, is_up=False)

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
                    self.save_mxdomain_in_cache(mxdomain, is_up=False)
                    self.logger.debug('The query name does not exist.')
                    print('The query name does not exist.')
                except dns.name.LabelTooLong:
                    self.logger.debug('The Label is too long')
                    print('The Label is too long')
                except dns.exception.Timeout:
                    print('dns timeout')
                    # save_mxdomain_in_cache(mxdomain)
                    self.save_mxdomain_in_cache(mxdomain, is_up=False)
                except Exception as e:
                    print(e)
        return valid_mxdomain

    def extract(self, obj, content, tag):
        extracted = []
        correls = obj.get_correlation('mail').get('mail', [])
        if len(correls) > 150:
            return []
        for m_id in correls:
            m = Mails.Mail(m_id[1:])
            mail = m.get_content()
            r_mail = re.compile(mail, flags=re.IGNORECASE)
            for row in self.regex_finditer(r_mail, m.get_global_id(), content):
                extracted.append([row[0], row[1], row[2], f'tag:{tag}'])
        return extracted

    # # TODO: sanitize mails
    def compute(self, message):
        item = self.get_obj()

        mails = self.regex_findall(self.email_regex, item.id, item.get_content())
        if mails:
            mxdomains_email = {}
            for mail in mails:
                if mail.startswith('-'):
                    mail = mail[1:]
                if len(mail) <= 100:
                    mxdomain = mail.rsplit('@', 1)[1].lower()
                    if mxdomain not in mxdomains_email:
                        mxdomains_email[mxdomain] = set()
                    mxdomains_email[mxdomain].add(mail.lower())

                # # TODO: add MAIL trackers

            valid_mx = self.check_mx_record(mxdomains_email.keys())
            # mx_tlds = {}
            to_tag = False
            date = self.obj.get_date()
            if self.obj.type == 'item':
                source = self.obj.get_source()
            else:
                source = None

            num_valid_email = 0
            for domain_mx in valid_mx:
                nb_mails = len(mxdomains_email[domain_mx])
                num_valid_email += nb_mails

                if self.obj.type in self.mail_correlation:
                    if source in self.mail_item_allowed_sources or source is None:
                        to_tag = True
                        for vmail in mxdomains_email[domain_mx]:
                            if vmail:
                                # mail = mail.strip()
                                mail = Mails.create(vmail)
                                if mail:
                                    mail.add(date, self.obj)

            msg = f'Checked {num_valid_email} e-mail(s);{self.obj.get_global_id()}'
            if num_valid_email >= self.mail_threshold or to_tag:
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

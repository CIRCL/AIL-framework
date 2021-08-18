#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Credential Module
=====================

This module is consuming the Redis-list created by the Categ module.

It apply credential regexes on item content and warn if above a threshold.

It also split the username and store it into redis for searching purposes.

Redis organization:
    uniqNumForUsername: unique number attached to unique username
    uniqNumForPath: unique number attached to unique path
        -> uniqNum are used to avoid string duplication
    AllCredentials: hashed set where keys are username and value are their uniq number
    AllCredentialsRev: the opposite of AllCredentials, uniqNum -> username
    AllPath: hashed set where keys are path and value are their uniq number
    AllPathRev: the opposite of AllPath, uniqNum -> path
    CredToPathMapping_uniqNumForUsername -> (set) -> uniqNumForPath

"""

##################################
# Import External packages
##################################
import os
import sys
import time
import re
import redis
from datetime import datetime
from pyfaup.faup import Faup

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from packages.Item import Item
from lib import ConfigLoader
from lib import regex_helper


class Credential(AbstractModule):
    """
    Credential module for AIL framework
    """

    # Split username with spec. char or with upper case, distinguish start with upper
    REGEX_CRED = "[a-z]+|[A-Z]{3,}|[A-Z]{1,2}[a-z]+|[0-9]+"
    REDIS_KEY_NUM_USERNAME = 'uniqNumForUsername'
    REDIS_KEY_NUM_PATH = 'uniqNumForUsername'
    REDIS_KEY_ALL_CRED_SET = 'AllCredentials'
    REDIS_KEY_ALL_CRED_SET_REV = 'AllCredentialsRev'
    REDIS_KEY_ALL_PATH_SET = 'AllPath'
    REDIS_KEY_ALL_PATH_SET_REV = 'AllPathRev'
    REDIS_KEY_MAP_CRED_TO_PATH = 'CredToPathMapping'


    def __init__(self):
        super(Credential, self).__init__()

        self.faup = Faup()

        self.regex_web = "((?:https?:\/\/)[\.-_0-9a-zA-Z]+\.[0-9a-zA-Z]+)"
        self.regex_cred = "[a-zA-Z0-9\\._-]+@[a-zA-Z0-9\\.-]+\.[a-zA-Z]{2,6}[\\rn :\_\-]{1,10}[a-zA-Z0-9\_\-]+"
        self.regex_site_for_stats = "@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}:"

        self.redis_cache_key = regex_helper.generate_redis_cache_key(self.module_name)

        # Database
        config_loader = ConfigLoader.ConfigLoader()
        self.server_cred = config_loader.get_redis_conn("ARDB_TermCred")
        self.server_statistics = config_loader.get_redis_conn("ARDB_Statistics")

        # Config values
        self.minimumLengthThreshold = config_loader.get_config_int("Credential", "minimumLengthThreshold")
        self.criticalNumberToAlert = config_loader.get_config_int("Credential", "criticalNumberToAlert")

        self.max_execution_time = 30

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 10

        # Send module state to logs
        self.redis_logger.info(f"Module {self.module_name} initialized")


    def compute(self, message):

        id, count = message.split()
        item = Item(id)

        item_content = item.get_content()

        # Extract all credentials
        all_credentials = regex_helper.regex_findall(self.module_name, self.redis_cache_key, self.regex_cred, item.get_id(), item_content, max_time=self.max_execution_time)

        if all_credentials:
            nb_cred = len(all_credentials)
            message = f'Checked {nb_cred} credentials found.'

            all_sites = regex_helper.regex_findall(self.module_name, self.redis_cache_key, self.regex_web, item.get_id(), item_content, max_time=self.max_execution_time)
            if all_sites:
                discovered_sites = ', '.join(all_sites)
                message += f' Related websites: {discovered_sites}'

            print(message)

            to_print = f'Credential;{item.get_source()};{item.get_date()};{item.get_basename()};{message};{item.get_id()}'

            #num of creds above tresh, publish an alert
            if nb_cred > self.criticalNumberToAlert:
                print(f"========> Found more than 10 credentials in this file : {item.get_id()}")
                self.redis_logger.warning(to_print)

                # Send to duplicate
                self.send_message_to_queue(item.get_id(), 'Duplicate')

                msg = f'infoleak:automatic-detection="credential";{item.get_id()}'
                self.send_message_to_queue(msg, 'Tags')

                site_occurence = regex_helper.regex_findall(self.module_name, self.redis_cache_key, self.regex_site_for_stats, item.get_id(), item_content, max_time=self.max_execution_time, r_set=False)

                creds_sites = {}

                for site in site_occurence:
                    site_domain = site[1:-1].lower()
                    if site_domain in creds_sites.keys():
                        creds_sites[site_domain] += 1
                    else:
                        creds_sites[site_domain] = 1

                for url in all_sites:
                    self.faup.decode(url)
                    domain = self.faup.get()['domain']
                    ## TODO: # FIXME: remove me, check faup versionb
                    try:
                        domain = domain.decode()
                    except:
                        pass
                    if domain in creds_sites.keys():
                        creds_sites[domain] += 1
                    else:
                        creds_sites[domain] = 1

                for site, num in creds_sites.items(): # Send for each different site to moduleStats

                    mssg = f'credential;{num};{site};{item.get_date()}'
                    print(mssg)
                    self.send_message_to_queue(mssg, 'ModuleStats')

                if all_sites:
                    discovered_sites = ', '.join(all_sites)
                    print(f"=======> Probably on : {discovered_sites}")

                date = datetime.now().strftime("%Y%m")
                for cred in all_credentials:
                    maildomains = re.findall("@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,20}", cred.lower())[0]
                    self.faup.decode(maildomains)
                    tld = self.faup.get()['tld']
                    ## TODO: # FIXME: remove me
                    try:
                        tld = tld.decode()
                    except:
                        pass
                    self.server_statistics.hincrby('credential_by_tld:'+date, tld, 1)
            else:
                self.redis_logger.info(to_print)
                print(f'found {nb_cred} credentials')

            # For searching credential in termFreq
            for cred in all_credentials:
                cred = cred.split('@')[0] #Split to ignore mail address

                # unique number attached to unique path
                uniq_num_path = self.server_cred.incr(Credential.REDIS_KEY_NUM_PATH)
                self.server_cred.hmset(Credential.REDIS_KEY_ALL_PATH_SET, {item.get_id(): uniq_num_path})
                self.server_cred.hmset(Credential.REDIS_KEY_ALL_PATH_SET_REV, {uniq_num_path: item.get_id()})

                # unique number attached to unique username
                uniq_num_cred = self.server_cred.hget(Credential.REDIS_KEY_ALL_CRED_SET, cred)
                if uniq_num_cred is None:
                    # cred do not exist, create new entries
                    uniq_num_cred = self.server_cred.incr(Credential.REDIS_KEY_NUM_USERNAME)
                    self.server_cred.hmset(Credential.REDIS_KEY_ALL_CRED_SET, {cred: uniq_num_cred})
                    self.server_cred.hmset(Credential.REDIS_KEY_ALL_CRED_SET_REV, {uniq_num_cred: cred})

                # Add the mapping between the credential and the path
                self.server_cred.sadd(Credential.REDIS_KEY_MAP_CRED_TO_PATH+'_'+str(uniq_num_cred), uniq_num_path)

                # Split credentials on capital letters, numbers, dots and so on
                # Add the split to redis, each split point towards its initial credential unique number
                splitedCred = re.findall(Credential.REGEX_CRED, cred)
                for partCred in splitedCred:
                    if len(partCred) > self.minimumLengthThreshold:
                        self.server_cred.sadd(partCred, uniq_num_cred)


if __name__ == '__main__':

    module = Credential()
    module.run()

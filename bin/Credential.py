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
import time
import os
import sys
import datetime
import re
import redis
from pyfaup.faup import Faup
from pubsublogger import publisher
import lib.regex_helper as regex_helper
import signal


##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from Helper import Process
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader


class Credential(AbstractModule):
    """
    Credential module for AIL framework
    """

    max_execution_time = 30

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
        self.server_cred = ConfigLoader.ConfigLoader().get_redis_conn("ARDB_TermCred")
        self.server_statistics = ConfigLoader.ConfigLoader().get_redis_conn("ARDB_Statistics")

        # Config values
        self.minimumLengthThreshold = ConfigLoader.ConfigLoader().get_config_int("Credential", "minimumLengthThreshold")
        self.criticalNumberToAlert = ConfigLoader.ConfigLoader().get_config_int("Credential", "criticalNumberToAlert")

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 10

        # Send module state to logs
        self.redis_logger.info(f"Module {self.module_name} initialized")


    def compute(self, message):

        item_id, count = message.split()

        item_content = Item.get_item_content(item_id)

        # Extract all credentials
        all_credentials = regex_helper.regex_findall(self.module_name, self.redis_cache_key, self.regex_cred, item_id, item_content, max_time=Credential.max_execution_time)

        if all_credentials: 
            nb_cred = len(all_credentials)
            message = f'Checked {nb_cred} credentials found.'
            
            all_sites = regex_helper.regex_findall(self.module_name, self.redis_cache_key, self.regex_web, item_id, item_content, max_time=Credential.max_execution_time)
            if all_sites:
                discovered_sites = ', '.join(all_sites)
                message += f' Related websites: {discovered_sites}'
            
            self.redis_logger.debug(message)

            to_print = f'Credential;{Item.get_source(item_id)};{Item.get_item_date(item_id)};{Item.get_item_basename(item_id)};{message};{item_id}'

            #num of creds above tresh, publish an alert
            if nb_cred > self.criticalNumberToAlert:
                self.redis_logger.debug(f"========> Found more than 10 credentials in this file : {item_id}")
                self.redis_logger.warning(to_print)
                
                # Send to duplicate
                self.process.populate_set_out(item_id, 'Duplicate')

                msg = f'infoleak:automatic-detection="credential";{item_id}'
                self.process.populate_set_out(msg, 'Tags')

                site_occurence = regex_helper.regex_findall(self.module_name, self.redis_cache_key, self.regex_site_for_stats, item_id, item_content, max_time=Credential.max_execution_time, r_set=False)

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
                    ## TODO: # FIXME: remove me
                    try:
                        domain = domain.decode()
                    except:
                        pass
                    if domain in creds_sites.keys():
                        creds_sites[domain] += 1
                    else:
                        creds_sites[domain] = 1

                for site, num in creds_sites.items(): # Send for each different site to moduleStats

                    mssg = f'credential;{num};{site};{Item.get_item_date(item_id)}'
                    self.redis_logger.debug(mssg)
                    self.process.populate_set_out(mssg, 'ModuleStats')

                if all_sites:
                    discovered_sites = ', '.join(all_sites)
                    self.redis_logger.debug(f"=======> Probably on : {discovered_sites}")

                date = datetime.datetime.now().strftime("%Y%m")
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
                self.redis_logger.debug(f'found {nb_cred} credentials')

            # For searching credential in termFreq
            for cred in all_credentials:
                cred = cred.split('@')[0] #Split to ignore mail address

                # unique number attached to unique path
                uniq_num_path = self.server_cred.incr(Credential.REDIS_KEY_NUM_PATH)
                self.server_cred.hmset(Credential.REDIS_KEY_ALL_PATH_SET, {item_id: uniq_num_path})
                self.server_cred.hmset(Credential.REDIS_KEY_ALL_PATH_SET_REV, {uniq_num_path: item_id})

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

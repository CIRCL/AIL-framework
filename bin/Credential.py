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

import time
import os
import sys
import datetime
import re
import redis
from pyfaup.faup import Faup

from pubsublogger import publisher
from Helper import Process

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import regex_helper

## LOAD CONFIG ##
config_loader = ConfigLoader.ConfigLoader()
server_cred = config_loader.get_redis_conn("ARDB_TermCred")
server_statistics = config_loader.get_redis_conn("ARDB_Statistics")

minimumLengthThreshold = config_loader.get_config_int("Credential", "minimumLengthThreshold")
criticalNumberToAlert = config_loader.get_config_int("Credential", "criticalNumberToAlert")
minTopPassList = config_loader.get_config_int("Credential", "minTopPassList")

config_loader = None
## -- ##

import signal

max_execution_time = 30

#split username with spec. char or with upper case, distinguish start with upper
REGEX_CRED = "[a-z]+|[A-Z]{3,}|[A-Z]{1,2}[a-z]+|[0-9]+"
REDIS_KEY_NUM_USERNAME = 'uniqNumForUsername'
REDIS_KEY_NUM_PATH = 'uniqNumForUsername'
REDIS_KEY_ALL_CRED_SET = 'AllCredentials'
REDIS_KEY_ALL_CRED_SET_REV = 'AllCredentialsRev'
REDIS_KEY_ALL_PATH_SET = 'AllPath'
REDIS_KEY_ALL_PATH_SET_REV = 'AllPathRev'
REDIS_KEY_MAP_CRED_TO_PATH = 'CredToPathMapping'

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"
    config_section = "Credential"
    module_name = "Credential"
    p = Process(config_section)
    publisher.info("Find credentials")

    faup = Faup()

    regex_web = "((?:https?:\/\/)[\.-_0-9a-zA-Z]+\.[0-9a-zA-Z]+)"
    #regex_cred = "[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}:[a-zA-Z0-9\_\-]+"
    regex_cred = "[a-zA-Z0-9\\._-]+@[a-zA-Z0-9\\.-]+\.[a-zA-Z]{2,6}[\\rn :\_\-]{1,10}[a-zA-Z0-9\_\-]+"
    regex_site_for_stats = "@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}:"

    redis_cache_key = regex_helper.generate_redis_cache_key(module_name)

    while True:
        message = p.get_from_set()

        if message is None:
            publisher.debug("Script Credential is Idling 10s")
            time.sleep(10)
            continue

        item_id, count = message.split()

        item_content = Item.get_item_content(item_id)

        # Extract all credentials
        all_credentials = regex_helper.regex_findall(module_name, redis_cache_key, regex_cred, item_content, max_time=max_execution_time)

        if not all_credentials:
            continue

        all_sites = regex_helper.regex_findall(module_name, redis_cache_key, regex_web, item_content, max_time=max_execution_time)

        message = 'Checked {} credentials found.'.format(len(all_credentials))
        if all_sites:
            message += ' Related websites: {}'.format( (', '.join(all_sites)) )
        print(message)

        to_print = 'Credential;{};{};{};{};{}'.format(Item.get_source(item_id), Item.get_item_date(item_id), Item.get_item_basename(item_id), message, item_id)


        #num of creds above tresh, publish an alert
        if len(all_credentials) > criticalNumberToAlert:
            print("========> Found more than 10 credentials in this file : {}".format( item_id ))
            publisher.warning(to_print)
            #Send to duplicate
            p.populate_set_out(item_id, 'Duplicate')

            msg = 'infoleak:automatic-detection="credential";{}'.format(item_id)
            p.populate_set_out(msg, 'Tags')

            site_occurence = regex_helper.regex_findall(module_name, redis_cache_key, regex_site_for_stats, item_content, max_time=max_execution_time, r_set=False)

            creds_sites = {}

            for site in site_occurence:
                site_domain = site[1:-1]
                if site_domain in creds_sites.keys():
                    creds_sites[site_domain] += 1
                else:
                    creds_sites[site_domain] = 1

            for url in all_sites:
                faup.decode(url)
                domain = faup.get()['domain']
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

                mssg = 'credential;{};{};{}'.format(num, site, Item.get_item_date(item_id))
                print(mssg)
                p.populate_set_out(mssg, 'ModuleStats')

            if all_sites:
                print("=======> Probably on : {}".format(', '.join(all_sites)))

            date = datetime.datetime.now().strftime("%Y%m")
            for cred in all_credentials:
                maildomains = re.findall("@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,20}", cred.lower())[0]
                faup.decode(maildomains)
                tld = faup.get()['tld']
                ## TODO: # FIXME: remove me
                try:
                    tld = tld.decode()
                except:
                    pass
                server_statistics.hincrby('credential_by_tld:'+date, tld, 1)
        else:
            publisher.info(to_print)
            print('found {} credentials'.format(len(all_credentials)))


        #for searching credential in termFreq
        for cred in all_credentials:
            cred = cred.split('@')[0] #Split to ignore mail address

            #unique number attached to unique path
            uniq_num_path = server_cred.incr(REDIS_KEY_NUM_PATH)
            server_cred.hmset(REDIS_KEY_ALL_PATH_SET, {item_id: uniq_num_path})
            server_cred.hmset(REDIS_KEY_ALL_PATH_SET_REV, {uniq_num_path: item_id})

            #unique number attached to unique username
            uniq_num_cred = server_cred.hget(REDIS_KEY_ALL_CRED_SET, cred)
            if uniq_num_cred is None: #cred do not exist, create new entries
                uniq_num_cred = server_cred.incr(REDIS_KEY_NUM_USERNAME)
                server_cred.hmset(REDIS_KEY_ALL_CRED_SET, {cred: uniq_num_cred})
                server_cred.hmset(REDIS_KEY_ALL_CRED_SET_REV, {uniq_num_cred: cred})

            #Add the mapping between the credential and the path
            server_cred.sadd(REDIS_KEY_MAP_CRED_TO_PATH+'_'+str(uniq_num_cred), uniq_num_path)

            #Split credentials on capital letters, numbers, dots and so on
            #Add the split to redis, each split point towards its initial credential unique number
            splitedCred = re.findall(REGEX_CRED, cred)
            for partCred in splitedCred:
                if len(partCred) > minimumLengthThreshold:
                    server_cred.sadd(partCred, uniq_num_cred)

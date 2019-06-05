#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Credential Module
=====================

This module is consuming the Redis-list created by the Categ module.

It apply credential regexes on paste content and warn if above a threshold.

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
import sys
from packages import Paste
from pubsublogger import publisher
from Helper import Process
import datetime
import re
import redis
from pyfaup.faup import Faup

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
    p = Process(config_section)
    publisher.info("Find credentials")

    minimumLengthThreshold = p.config.getint("Credential", "minimumLengthThreshold")

    faup = Faup()
    server_cred = redis.StrictRedis(
        host=p.config.get("ARDB_TermCred", "host"),
        port=p.config.get("ARDB_TermCred", "port"),
        db=p.config.get("ARDB_TermCred", "db"),
        decode_responses=True)

    server_statistics = redis.StrictRedis(
        host=p.config.get("ARDB_Statistics", "host"),
        port=p.config.getint("ARDB_Statistics", "port"),
        db=p.config.getint("ARDB_Statistics", "db"),
        decode_responses=True)

    criticalNumberToAlert = p.config.getint("Credential", "criticalNumberToAlert")
    minTopPassList = p.config.getint("Credential", "minTopPassList")

    regex_web = "((?:https?:\/\/)[-_0-9a-zA-Z]+\.[0-9a-zA-Z]+)"
    #regex_cred = "[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}:[a-zA-Z0-9\_\-]+"
    regex_cred = "[a-zA-Z0-9\\._-]+@[a-zA-Z0-9\\.-]+\.[a-zA-Z]{2,6}[\\rn :\_\-]{1,10}[a-zA-Z0-9\_\-]+"
    regex_site_for_stats = "@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}:"

    while True:
        message = p.get_from_set()
        if message is None:
            publisher.debug("Script Credential is Idling 10s")
            #print('sleeping 10s')
            time.sleep(10)
            continue

        filepath, count = message.split(' ')

        paste = Paste.Paste(filepath)
        content = paste.get_p_content()
        creds = set(re.findall(regex_cred, content))

        if len(creds) == 0:
            continue

        sites= re.findall(regex_web, content) #Use to count occurences
        sites_set = set(re.findall(regex_web, content))

        message = 'Checked {} credentials found.'.format(len(creds))
        if sites_set:
            message += ' Related websites: {}'.format( (', '.join(sites_set)) )

        to_print = 'Credential;{};{};{};{};{}'.format(paste.p_source, paste.p_date, paste.p_name, message, paste.p_rel_path)

        print('\n '.join(creds))

        #num of creds above tresh, publish an alert
        if len(creds) > criticalNumberToAlert:
            print("========> Found more than 10 credentials in this file : {}".format( filepath ))
            publisher.warning(to_print)
            #Send to duplicate
            p.populate_set_out(filepath, 'Duplicate')

            msg = 'infoleak:automatic-detection="credential";{}'.format(filepath)
            p.populate_set_out(msg, 'Tags')

            #Put in form, count occurences, then send to moduleStats
            creds_sites = {}
            site_occurence = re.findall(regex_site_for_stats, content)
            for site in site_occurence:
                site_domain = site[1:-1]
                if site_domain in creds_sites.keys():
                    creds_sites[site_domain] += 1
                else:
                    creds_sites[site_domain] = 1

            for url in sites:
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

                mssg = 'credential;{};{};{}'.format(num, site, paste.p_date)
                print(mssg)
                p.populate_set_out(mssg, 'ModuleStats')

            if sites_set:
                print("=======> Probably on : {}".format(', '.join(sites_set)))

            date = datetime.datetime.now().strftime("%Y%m")
            for cred in creds:
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
            print('found {} credentials'.format(len(creds)))


        #for searching credential in termFreq
        for cred in creds:
            cred = cred.split('@')[0] #Split to ignore mail address

            #unique number attached to unique path
            uniq_num_path = server_cred.incr(REDIS_KEY_NUM_PATH)
            server_cred.hmset(REDIS_KEY_ALL_PATH_SET, {filepath: uniq_num_path})
            server_cred.hmset(REDIS_KEY_ALL_PATH_SET_REV, {uniq_num_path: filepath})

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

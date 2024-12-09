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
from pyfaup.faup import Faup

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib import ConfigLoader


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

        self.regex_web = r"((?:https?:\/\/)[\.-_0-9a-zA-Z]+\.[0-9a-zA-Z]+)"
        self.regex_cred = r"[a-zA-Z0-9\\._-]+@[a-zA-Z0-9\\.-]+\.[a-zA-Z]{2,6}[\\rn :\_\-]{1,10}[a-zA-Z0-9\_\-]+"
        self.regex_site_for_stats = r"@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}:"

        # Database
        config_loader = ConfigLoader.ConfigLoader()
        # self.server_cred = config_loader.get_redis_conn("_TermCred")

        # Config values
        self.minimumLengthThreshold = config_loader.get_config_int("Credential", "minimumLengthThreshold")
        self.criticalNumberToAlert = config_loader.get_config_int("Credential", "criticalNumberToAlert")

        self.max_execution_time = 30

        # Waiting time in seconds between to message processed
        self.pending_seconds = 10

        # Send module state to logs
        self.logger.info(f"Module {self.module_name} initialized")

    def compute(self, message):

        obj = self.get_obj()

        content = obj.get_content()

        # TODO: USE SETS
        # Extract all credentials
        all_credentials = self.regex_findall(self.regex_cred, obj.get_id(), content)
        if all_credentials:
            nb_cred = len(all_credentials)
            message = f'Checked {nb_cred} credentials found.'

            all_sites = self.regex_findall(self.regex_web, obj.get_id(), content, r_set=True)
            if all_sites:
                discovered_sites = ', '.join(all_sites)
                message += f' Related websites: {discovered_sites}'

            print(message)

            # num of creds above threshold, publish an alert
            if nb_cred > self.criticalNumberToAlert:
                print(f"========> Found more than 10 credentials in this file : {self.obj.get_global_id()}")

                tag = 'infoleak:automatic-detection="credential"'
                self.add_message_to_queue(message=tag, queue='Tags')

                site_occurrence = self.regex_findall(self.regex_site_for_stats, obj.get_id(), content)

                creds_sites = {}

                for site in site_occurrence:
                    site_domain = site[1:-1].lower()
                    if site_domain in creds_sites.keys():
                        creds_sites[site_domain] += 1
                    else:
                        creds_sites[site_domain] = 1

                for url in all_sites:
                    self.faup.decode(url)
                    domain = self.faup.get()['domain']
                    # # TODO: # FIXME: remove me, check faup versionb
                    try:
                        domain = domain.decode()
                    except:
                        pass
                    if domain in creds_sites.keys():
                        creds_sites[domain] += 1
                    else:
                        creds_sites[domain] = 1

                # for site, num in creds_sites.items(): # Send for each different site to moduleStats
                #
                #     mssg = f'credential;{num};{site};{item.get_date()}'
                #     print(mssg)
                #     self.add_message_to_queue(mssg, 'ModuleStats')

                if all_sites:
                    discovered_sites = ', '.join(all_sites)
                    print(f"=======> Probably on : {discovered_sites}")

                # date = datetime.now().strftime("%Y%m")
                # nb_tlds = {}
                # for cred in all_credentials:
                #     maildomains = re.findall(r"@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,20}", cred.lower())[0]
                #     self.faup.decode(maildomains)
                #     tld = self.faup.get()['tld']
                #     # # TODO: # FIXME: remove me
                #     try:
                #         tld = tld.decode()
                #     except:
                #         pass
                #     nb_tlds[tld] = nb_tlds.get(tld, 0) + 1
                # for tld in nb_tlds:
                #     Statistics.add_module_tld_stats_by_date('credential', date, tld, nb_tlds[tld])
            else:
                print(f'found {nb_cred} credentials {self.obj.get_global_id()}')

            # # TODO: # FIXME: TEMP DESABLE
            # # For searching credential in termFreq
            # for cred in all_credentials:
            #     cred = cred.split('@')[0] #Split to ignore mail address
            #
            #     # unique number attached to unique path
            #     uniq_num_path = self.server_cred.incr(Credential.REDIS_KEY_NUM_PATH)
            #     self.server_cred.hmset(Credential.REDIS_KEY_ALL_PATH_SET, {item.get_id(): uniq_num_path})
            #     self.server_cred.hmset(Credential.REDIS_KEY_ALL_PATH_SET_REV, {uniq_num_path: item.get_id()})
            #
            #     # unique number attached to unique username
            #     uniq_num_cred = self.server_cred.hget(Credential.REDIS_KEY_ALL_CRED_SET, cred)
            #     if uniq_num_cred is None:
            #         # cred do not exist, create new entries
            #         uniq_num_cred = self.server_cred.incr(Credential.REDIS_KEY_NUM_USERNAME)
            #         self.server_cred.hmset(Credential.REDIS_KEY_ALL_CRED_SET, {cred: uniq_num_cred})
            #         self.server_cred.hmset(Credential.REDIS_KEY_ALL_CRED_SET_REV, {uniq_num_cred: cred})
            #
            #     # Add the mapping between the credential and the path
            #     self.server_cred.sadd(Credential.REDIS_KEY_MAP_CRED_TO_PATH+'_'+str(uniq_num_cred), uniq_num_path)
            #
            #     # Split credentials on capital letters, numbers, dots and so on
            #     # Add the split to redis, each split point towards its initial credential unique number
            #     splitedCred = re.findall(Credential.REGEX_CRED, cred)
            #     for partCred in splitedCred:
            #         if len(partCred) > self.minimumLengthThreshold:
            #             self.server_cred.sadd(partCred, uniq_num_cred)


if __name__ == '__main__':

    module = Credential()
    module.run()

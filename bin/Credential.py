#!/usr/bin/env python2
# -*-coding:UTF-8 -*

"""
The Credential Module
=====================

This module is consuming the Redis-list created by the Categ module.

It apply credential regexes on paste content and warn if above a threshold.

"""

import time
import sys
from packages import Paste
from pubsublogger import publisher
from Helper import Process
import re
from pyfaup.faup import Faup

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"
    config_section = "Credential"
    p = Process(config_section)
    publisher.info("Find credentials")

    faup = Faup()

    critical = 8

    regex_web = "((?:https?:\/\/)[-_0-9a-zA-Z]+\.[0-9a-zA-Z]+)"
    regex_cred = "[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}:[a-zA-Z0-9\_\-]+"
    regex_site_for_stats = "@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}:"
    while True:
        message = p.get_from_set()
        if message is None:
            publisher.debug("Script Credential is Idling 10s")
            time.sleep(10)
            continue

        filepath, count = message.split()

        if count < 5:
            # Less than 5 matches from the top password list, false positive.
            continue

        paste = Paste.Paste(filepath)
        content = paste.get_p_content()
        creds = set(re.findall(regex_cred, content))
        if len(creds) == 0:
            continue

        sites= re.findall(regex_web, content) #Use to count occurences
        sites_set = set(re.findall(regex_web, content))

        message = 'Checked {} credentials found.'.format(len(creds))
        if sites_set:
            message += ' Related websites: {}'.format(', '.join(sites_set))

        to_print = 'Credential;{};{};{};{};{}'.format(paste.p_source, paste.p_date, paste.p_name, message, paste.p_path)

        print('\n '.join(creds))

        if len(creds) > critical:
            print("========> Found more than 10 credentials in this file : {}".format(filepath))
            publisher.warning(to_print)
            #Send to duplicate
            p.populate_set_out(filepath, 'Duplicate')
            #Send to BrowseWarningPaste
            p.populate_set_out('credential;{}'.format(filepath), 'BrowseWarningPaste')
            
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
                if domain in creds_sites.keys():
                    creds_sites[domain] += 1
                else:
                    creds_sites[domain] = 1

            for site, num in creds_sites.iteritems(): # Send for each different site to moduleStats
                print 'credential;{};{};{}'.format(num, site, paste.p_date)
                p.populate_set_out('credential;{};{};{}'.format(num, site, paste.p_date), 'ModuleStats')

            if sites_set:
                print("=======> Probably on : {}".format(', '.join(sites_set)))
        else:
            publisher.info(to_print)

#!/usr/bin/env python2
# -*-coding:UTF-8 -*
import time
from packages import Paste
from pubsublogger import publisher
from Helper import Process
import re

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"
    config_section = "Credential"
    p = Process(config_section)
    publisher.info("Find credentials")

    critical = 8

    regex_web = "((?:https?:\/\/)[-_0-9a-zA-Z]+\.[0-9a-zA-Z]+)"
    regex_cred = "[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}:[a-zA-Z0-9\_\-]+"
    while True:
        message = p.get_from_set()
        if message is None:
            publisher.debug("Script Credential is Idling 10s")
            print('Sleeping')
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

        sites = set(re.findall(regex_web, content))

        message = 'Checked {} credentials found.'.format(len(creds))
        if sites:
            message += ' Related websites: {}'.format(', '.join(sites))

        to_print = 'Credential;{};{};{};{}'.format(paste.p_source, paste.p_date, paste.p_name, message)

        print('\n '.join(creds))

        if len(creds) > critical:
            print("========> Found more than 10 credentials in this file : {}".format(filepath))
            publisher.warning(to_print)
            if sites:
                print("=======> Probably on : {}".format(', '.join(sites)))
        else:
            publisher.info(to_print)

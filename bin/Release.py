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
    config_section = "Release"
    p = Process(config_section)
    publisher.info("Release scripts to find release names")

    movie = "[a-zA-Z0-9.]+\.[0-9]{4}.[a-zA-Z0-9.]+\-[a-zA-Z]+"
    tv = "[a-zA-Z0-9.]+\.S[0-9]{2}E[0-9]{2}.[a-zA-Z0-9.]+\.[a-zA-Z0-9.]+\-[a-zA-Z0-9]+"
    xxx = "[a-zA-Z0-9._]+.XXX.[a-zA-Z0-9.]+\-[a-zA-Z0-9]+"

    regexs = [movie, tv, xxx]

    regex = '|'.join(regexs)
    while True:
        filepath = p.get_from_set()
        if filepath is None:
            publisher.debug("Script Release is Idling 10s")
            print 'Sleeping'
            time.sleep(10)
            continue

        paste = Paste.Paste(filepath)
        content = paste.get_p_content()
        releases = set(re.findall(regex, content))
        if len(releases) == 0:
            continue

        to_print = 'Release;{};{};{};{} releases'.format(paste.p_source, paste.p_date, paste.p_name, len(releases))
        if len(releases) > 30:
            publisher.warning(to_print)
        else:
            publisher.info(to_print)

#!/usr/bin/env python3
# -*-coding:UTF-8 -*
import time
from packages import Paste
from pubsublogger import publisher
from Helper import Process
import re

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"
    config_section = "SourceCode"
    p = Process(config_section)
    publisher.info("Finding Source Code")

    critical = 0 # AS TO BE IMPORTANT, MIGHT BE REMOVED

    #RELEVANTS LANGUAGES
    shell = "[a-zA-Z0-9]+@[a-zA-Z0-9\-]+\:\~\$"
    c = "\#include\ \<[a-z\/]+.h\>"
    php = "\<\?php"
    python = "import\ [\w]+"
    bash = "#!\/[\w]*\/bash"
    javascript = "function\(\)"
    ruby = "require \ [\w]+"
    adr = "0x[a-f0-9]{2}"

    #asm = "\"((?s).{1}x[0-9a-f]{2}){3,}" ISSUES WITH FINDALL, pattern like \x54\xaf\x23\..

    languages = [shell, c, php, bash, python, javascript, bash, ruby, adr]
    regex = '|'.join(languages)
    print(regex)

    while True:
        message = p.get_from_set()
        if message is None:
            publisher.debug("Script Source Code is Idling 10s")
            print('Sleeping')
            time.sleep(10)
            continue

        filepath, count = message.split()

        paste = Paste.Paste(filepath)
        content = paste.get_p_content()
        match_set = set(re.findall(regex, content))
        if len(match_set) == 0:
            continue

        to_print = 'SourceCode;{};{};{};{}'.format(paste.p_source, paste.p_date, paste.p_name, message)

        if len(match_set) > critical:
            publisher.warning(to_print)
        else:
            publisher.info(to_print)

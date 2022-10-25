#!/usr/bin/env python3
# -*-coding:UTF-8 -*
import time
from lib.objects.Items import Item
from pubsublogger import publisher
from Helper import Process
import re

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"
    config_section = "SourceCode"
    p = Process(config_section)
    publisher.info("Finding Source Code")

    critical = 0  # AS TO BE IMPORTANT, MIGHT BE REMOVED

    # RELEVANT LANGUAGES
    shell = r"[a-zA-Z0-9]+@[a-zA-Z0-9\-]+\:\~\$"
    c = r"\#include\ \<[a-z\/]+.h\>"
    php = r"\<\?php"
    python = r"import\ [\w]+"
    bash = r"#!\/[\w]*\/bash"
    javascript = r"function\(\)"
    ruby = r"require \ [\w]+"
    adr = r"0x[a-f0-9]{2}"

    # asm = r"\"((?s).{1}x[0-9a-f]{2}){3,}" ISSUES WITH FINDALL, pattern like \x54\xaf\x23\..

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

        item = Item(filepath)
        content = item.get_content()
        match_set = set(re.findall(regex, content))
        if len(match_set) == 0:
            continue

        to_print = f'SourceCode;{item.get_source()};{item.get_date()};{item.get_basename()};{item.get_id()}'

        if len(match_set) > critical:
            publisher.warning(to_print)
        else:
            publisher.info(to_print)

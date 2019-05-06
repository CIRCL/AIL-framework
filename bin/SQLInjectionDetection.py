#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The SQLInjectionDetection Module
================================

This module is consuming the Redis-list created by the Web module.

It test different possibility to makes some sqlInjection.

"""

import time
import datetime
import redis
import string
import urllib.request
import re
from pubsublogger import publisher
from Helper import Process
from packages import Paste
from pyfaup.faup import Faup

# Config Var

regex_injection = []
word_injection = []
word_injection_suspect = []

# Classic atome injection
regex_injection1 = "([[AND |OR ]+[\'|\"]?[0-9a-zA-Z]+[\'|\"]?=[\'|\"]?[0-9a-zA-Z]+[\'|\"]?])"
regex_injection.append(regex_injection1)

# Time-based attack
regex_injection2 = ["SLEEP\([0-9]+", "BENCHMARK\([0-9]+", "WAIT FOR DELAY ", "WAITFOR DELAY"]
regex_injection2 = re.compile('|'.join(regex_injection2))
regex_injection.append(regex_injection2)

# Interesting  keyword
word_injection1 = [" IF ", " ELSE ", " CASE ", " WHEN ", " END ", " UNION ", "SELECT ", " FROM ", " ORDER BY ", " WHERE ", " DELETE ", " DROP ", " UPDATE ", " EXEC "]
word_injection.append(word_injection1)

# Database special keywords
word_injection2 = ["@@version", "POW(", "BITAND(", "SQUARE("]
word_injection.append(word_injection2)

# Html keywords
word_injection3 = ["<script>"]
word_injection.append(word_injection3)

# Suspect char
word_injection_suspect1 = ["\'", "\"", ";", "<", ">"]
word_injection_suspect += word_injection_suspect1

# Comment
word_injection_suspect2 = ["--", "#", "/*"]
word_injection_suspect += word_injection_suspect2

def analyse(url, path):
    faup.decode(url)
    url_parsed = faup.get()

    resource_path = url_parsed['resource_path']
    query_string = url_parsed['query_string']

    result_path = 0
    result_query = 0

    if resource_path is not None:
        ## TODO: # FIXME: remove me
        try:
            resource_path = resource_path.decode()
        except:
            pass
        result_path = is_sql_injection(resource_path)

    if query_string is not None:
        ## TODO: # FIXME: remove me
        try:
            query_string = query_string.decode()
        except:
            pass
        result_query = is_sql_injection(query_string)

    if (result_path > 0) or (result_query > 0):
        paste = Paste.Paste(path)
        if (result_path > 1) or (result_query > 1):
            print("Detected SQL in URL: ")
            print(urllib.request.unquote(url))
            to_print = 'SQLInjection;{};{};{};{};{}'.format(paste.p_source, paste.p_date, paste.p_name, "Detected SQL in URL", paste.p_rel_path)
            publisher.warning(to_print)
            #Send to duplicate
            p.populate_set_out(path, 'Duplicate')

            msg = 'infoleak:automatic-detection="sql-injection";{}'.format(path)
            p.populate_set_out(msg, 'Tags')

            #statistics
            tld = url_parsed['tld']
            if tld is not None:
                ## TODO: # FIXME: remove me
                try:
                    tld = tld.decode()
                except:
                    pass
                date = datetime.datetime.now().strftime("%Y%m")
                server_statistics.hincrby('SQLInjection_by_tld:'+date, tld, 1)

        else:
            print("Potential SQL injection:")
            print(urllib.request.unquote(url))
            to_print = 'SQLInjection;{};{};{};{};{}'.format(paste.p_source, paste.p_date, paste.p_name, "Potential SQL injection", paste.p_rel_path)
            publisher.info(to_print)


# Try to detect if the url passed might be an sql injection by appliying the regex
# defined above on it.
def is_sql_injection(url_parsed):
    line = urllib.request.unquote(url_parsed)
    line = str.upper(line)
    result = []
    result_suspect = []

    for regex in regex_injection:
        temp_res = re.findall(regex, line)
        if len(temp_res)>0:
            result.append(temp_res)

    for word_list in word_injection:
        for word in word_list:
            temp_res = str.find(line, str.upper(word))
            if temp_res!=-1:
                result.append(line[temp_res:temp_res+len(word)])

    for word in word_injection_suspect:
        temp_res = str.find(line, str.upper(word))
        if temp_res!=-1:
            result_suspect.append(line[temp_res:temp_res+len(word)])

    if len(result)>0:
        print(result)
        return 2
    elif len(result_suspect)>0:
        print(result_suspect)
        return 1
    else:
        return 0



if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'SQLInjectionDetection'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Try to detect SQL injection")

    server_statistics = redis.StrictRedis(
        host=p.config.get("ARDB_Statistics", "host"),
        port=p.config.getint("ARDB_Statistics", "port"),
        db=p.config.getint("ARDB_Statistics", "db"),
        decode_responses=True)

    faup = Faup()

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()

        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(10)
            continue

        else:
            # Do something with the message from the queue
            url, date, path = message.split()
            analyse(url, path)

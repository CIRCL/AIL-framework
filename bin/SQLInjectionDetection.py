#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
    Template for new modules
"""

import time
import sys
import string
import datetime
import redis
import os
import urllib2
import re
from pubsublogger import publisher
from Helper import Process
from packages import Paste
from pyfaup.faup import Faup

# Config Var

regex_injection = []
word_injection = []

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

# Comment
word_injection2 = ["--", "#", "/*"]
word_injection.append(word_injection2)

# Database special keywords
word_injection3 = ["@@version", "POW(", "BITAND(", "SQUARE("]
word_injection.append(word_injection3)

# Html keywords
word_injection4 = ["<script>"]
word_injection.append(word_injection4)

# Suspect char
word_injection_suspect = ["\'", "\"", ";", "<", ">"]


def analyse(url, path):
    faup.decode(url)
    url_parsed = faup.get()

    resource_path = url_parsed['resource_path']
    query_string = url_parsed['query_string']

    result_path = 0
    result_query = 0

    if resource_path is not None:
        result_path = is_sql_injection(resource_path)

    if query_string is not None:
        result_query = is_sql_injection(query_string)

    if (result_path > 0) or (result_query > 0):
        paste = Paste.Paste(path)
        if (result_path > 1) or (result_query > 1):
            print "Detected SQL in URL: "
            print url
            to_print = 'SQLInjection;{};{};{};{}'.format(paste.p_source, paste.p_date, paste.p_name, "Detected SQL in URL")
            publisher.warning(to_print)
        else: 
            print "Potential SQL injection:"
            print url
            to_print = 'SQLInjection;{};{};{};{}'.format(paste.p_source, paste.p_date, paste.p_name, "Potential SQL injection")
            publisher.info(to_print)
    

def is_sql_injection(url_parsed):
    line = urllib2.unquote(url_parsed)
    line = string.upper(line)
    result = []
    result_suspect = []

    for regex in regex_injection:
        temp_res = re.findall(regex, line)
        if len(temp_res)>0:
            result.append(temp_res)

    for word_list in word_injection:
        for word in word_list:
            temp_res = string.find(line, string.upper(word))
            if temp_res!=-1:
                result.append(line[temp_res:temp_res+len(word)])

    for word in word_injection_suspect:
        temp_res = string.find(line, string.upper(word))
        if temp_res!=-1:
            result_suspect.append(line[temp_res:temp_res+len(word)])

    if len(result)>0:
        print result
        return 2
    elif len(result_suspect)>0:
        print result_suspect
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

    # REDIS #
    r_serv1 = redis.StrictRedis(
        host=p.config.get("Redis_Level_DB", "host"),
        port=p.config.get("Redis_Level_DB", "port"),
        db=p.config.get("Redis_Level_DB", "db"))
 

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
            analyse(url, path)	#Scheme analysis

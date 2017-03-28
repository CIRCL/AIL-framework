#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
This Module is used for term frequency.

"""
import redis
import time
from pubsublogger import publisher
from packages import lib_words
import os
import datetime
import calendar
import re

from Helper import Process

# Config Variables
BlackListTermsSet_Name = "BlackListSetTermSet"
TrackedTermsSet_Name = "TrackedSetTermSet"
TrackedRegexSet_Name = "TrackedRegexSet"
top_term_freq_max_set_cardinality = 20 # Max cardinality of the terms frequences set
oneDay = 60*60*24
top_termFreq_setName_day = ["TopTermFreq_set_day_", 1]
top_termFreq_setName_week = ["TopTermFreq_set_week", 7]
top_termFreq_setName_month = ["TopTermFreq_set_month", 31]
top_termFreq_set_array = [top_termFreq_setName_day,top_termFreq_setName_week, top_termFreq_setName_month]


if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'RegexForTermsFrequency'
    p = Process(config_section)

    # REDIS #
    server_term = redis.StrictRedis(
        host=p.config.get("Redis_Level_DB_TermFreq", "host"),
        port=p.config.get("Redis_Level_DB_TermFreq", "port"),
        db=p.config.get("Redis_Level_DB_TermFreq", "db"))

    # FUNCTIONS #
    publisher.info("RegexForTermsFrequency script started")

    #compile the regex
    dico_regex = {}
    for regex_str in server_term.smembers(TrackedRegexSet_Name):
        dico_regex[regex_str] = re.compile(regex_str)


    message = p.get_from_set()

    # Regex Frequency
    while True:

        if message is not None:
            filename, timestamp, word = message.split()
            curr_set = top_termFreq_setName_day[0] + str(timestamp)

            #iterate the word with the regex
            for regex_str, compiled_regex in dico_regex.items():
                matched = compiled_regex.match(word)
                if word == "amzinggg":
                    print("matched")
                    server_term.incr("thisistest")

                if matched is not None: #there is a match
                    matched = matched.group(0)
                    # Add in Regex track set only if term is not in the blacklist
                    if matched not in server_term.smembers(BlackListTermsSet_Name):
                        set_name = 'regex_' + regex_str
                        new_to_the_set = server_term.sadd(set_name, filename)
                        new_to_the_set = True if new_to_the_set == 1 else False

                        #consider the num of occurence of this term
                        regex_value = int(server_term.hincrby(timestamp, regex_str, int(1)))
                        #1 term per paste
                        if new_to_the_set:
                            regex_value_perPaste = int(server_term.hincrby("per_paste_" + str(timestamp), regex_str, int(1)))
                            server_term.zincrby("per_paste_" + curr_set, regex_str, float(1))
                    server_term.zincrby(curr_set, regex_str, float(1))


        else:
            publisher.debug("Script RegexForTermsFrequency is Idling")
            print "sleeping"
            time.sleep(5)
        message = p.get_from_set()

#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
This Module is used for term frequency.
It processes every paste coming from the global module and test the sets
supplied in  the term webpage.

"""
import redis
import time
from pubsublogger import publisher
from packages import lib_words
from packages import Paste
import os
import datetime
import calendar
import re
import ast
from Helper import Process

# Email notifications
from NotificationHelper import *

# Config Variables
BlackListTermsSet_Name = "BlackListSetTermSet"
TrackedTermsSet_Name = "TrackedSetTermSet"
TrackedRegexSet_Name = "TrackedRegexSet"
TrackedSetSet_Name = "TrackedSetSet"

top_term_freq_max_set_cardinality = 20 # Max cardinality of the terms frequences set
oneDay = 60*60*24
top_termFreq_setName_day = ["TopTermFreq_set_day_", 1]
top_termFreq_setName_week = ["TopTermFreq_set_week", 7]
top_termFreq_setName_month = ["TopTermFreq_set_month", 31]
top_termFreq_set_array = [top_termFreq_setName_day,top_termFreq_setName_week, top_termFreq_setName_month]

TrackedTermsNotificationTagsPrefix_Name = "TrackedNotificationTags_"

# create direct link in mail
full_paste_url = "/showsavedpaste/?paste="

def add_quote_inside_tab(tab):
    quoted_tab = "["
    for elem in tab[1:-1].split(','):
        elem = elem.lstrip().strip()
        quoted_tab += "\'{}\', ".format(elem)
    quoted_tab = quoted_tab[:-2] #remove trailing ,
    quoted_tab += "]"
    return str(quoted_tab)

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'SetForTermsFrequency'
    p = Process(config_section)

    # REDIS #
    server_term = redis.StrictRedis(
        host=p.config.get("ARDB_TermFreq", "host"),
        port=p.config.get("ARDB_TermFreq", "port"),
        db=p.config.get("ARDB_TermFreq", "db"),
        decode_responses=True)

    # FUNCTIONS #
    publisher.info("RegexForTermsFrequency script started")

    # create direct link in mail
    full_paste_url = p.config.get("Notifications", "ail_domain") + full_paste_url

    #get the dico and matching percent
    dico_percent = {}
    dico_set_tab = {}
    dico_setname_to_redis = {}
    for set_str in server_term.smembers(TrackedSetSet_Name):
        tab_set = set_str[1:-1]
        tab_set = add_quote_inside_tab(tab_set)
        perc_finder = re.compile("\[[0-9]{1,3}\]").search(tab_set)
        if perc_finder is not None:
            match_percent = perc_finder.group(0)[1:-1]
            dico_percent[tab_set] = float(match_percent)
            dico_set_tab[tab_set] = ast.literal_eval(tab_set)
            dico_setname_to_redis[tab_set] = set_str
        else:
            continue

    message = p.get_from_set()

    while True:

        if message is not None:
            filename = message
            temp = filename.split('/')
            timestamp = calendar.timegm((int(temp[-4]), int(temp[-3]), int(temp[-2]), 0, 0, 0))
            content = Paste.Paste(filename).get_p_content()

            curr_set = top_termFreq_setName_day[0] + str(timestamp)

            #iterate over the words of the file
            match_dico = {}
            for word in content.split():
                for cur_set, array_set in dico_set_tab.items():
                    for w_set in array_set[:-1]: #avoid the percent matching
                        if word == w_set:
                            try:
                                match_dico[str(array_set)] += 1
                            except KeyError:
                                match_dico[str(array_set)] = 1

            #compute matching %
            for the_set, matchingNum in match_dico.items():
                eff_percent = float(matchingNum) / float((len(ast.literal_eval(the_set))-1)) * 100 #-1 bc if the percent matching
                if eff_percent >= dico_percent[the_set]:
                    # Send a notification only when the member is in the set
                    if dico_setname_to_redis[str(the_set)] in server_term.smembers(TrackedTermsNotificationEnabled_Name):

                        # create mail body
                        mail_body = ("AIL Framework,\n"
                                    "New occurrence for term: " + dico_setname_to_redis[str(the_set)] + "\n"
                                    ''+full_paste_url + filename)

                        # Send to every associated email adress
                        for email in server_term.smembers(TrackedTermsNotificationEmailsPrefix_Name + dico_setname_to_redis[str(the_set)]):
                            sendEmailNotification(email, 'Term', mail_body)

                    # tag paste
                    for tag in server_term.smembers(TrackedTermsNotificationTagsPrefix_Name + dico_setname_to_redis[str(the_set)]):
                        msg = '{};{}'.format(tag, filename)
                        p.populate_set_out(msg, 'Tags')

                    print(the_set, "matched in", filename)
                    set_name = 'set_' + dico_setname_to_redis[the_set]
                    new_to_the_set = server_term.sadd(set_name, filename)
                    new_to_the_set = True if new_to_the_set == 1 else False

                    #consider the num of occurence of this set
                    set_value = int(server_term.hincrby(timestamp, dico_setname_to_redis[the_set], int(1)))

                    # FIXME - avoid using per paste as a set is checked over the entire paste
                    #1 term per paste
                    if new_to_the_set:
                        set_value_perPaste = int(server_term.hincrby("per_paste_" + str(timestamp), dico_setname_to_redis[the_set], int(1)))
                        server_term.zincrby("per_paste_" + curr_set, dico_setname_to_redis[the_set], float(1))
                server_term.zincrby(curr_set, dico_setname_to_redis[the_set], float(1))


        else:
            publisher.debug("Script RegexForTermsFrequency is Idling")
            print("sleeping")
            time.sleep(5)
        message = p.get_from_set()

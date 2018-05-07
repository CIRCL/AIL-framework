#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The WebStats Module
======================

This module makes stats on URL recolted from the web module.
It consider the TLD, Domain and protocol.

"""

import time
import datetime
import redis
import os
from packages import lib_words
from packages.Date import Date
from pubsublogger import publisher
from Helper import Process
from pyfaup.faup import Faup

# Config Var
threshold_total_sum = 200 # Above this value, a keyword is eligible for a progression
threshold_increase = 1.0  # The percentage representing the keyword occurence since num_day_to_look
max_set_cardinality = 10  # The cardinality of the progression set
num_day_to_look = 5       # the detection of the progression start num_day_to_look in the past

def analyse(server, field_name, date, url_parsed):
    field = url_parsed[field_name]
    if field is not None:
        field = field.decode('utf8')
        server.hincrby(field, date, 1)
        if field_name == "domain": #save domain in a set for the monthly plot
            domain_set_name = "domain_set_" + date[0:6]
            server.sadd(domain_set_name, field)
            print("added in " + domain_set_name +": "+ field)

def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return date_list

# Compute the progression for one keyword
def compute_progression_word(server, num_day, keyword):
    date_range = get_date_range(num_day)
    # check if this keyword is eligible for progression
    keyword_total_sum = 0
    value_list = []
    for date in date_range: # get value up to date_range
        curr_value = server.hget(keyword, date)
        value_list.append(int(curr_value if curr_value is not None else 0))
        keyword_total_sum += int(curr_value) if curr_value is not None else 0
    oldest_value = value_list[-1] if value_list[-1] != 0 else 1 #Avoid zero division

    # The progression is based on the ratio: value[i] / value[i-1]
    keyword_increase = 0
    value_list_reversed = value_list[:]
    value_list_reversed.reverse()
    for i in range(1, len(value_list_reversed)):
        divisor = value_list_reversed[i-1] if value_list_reversed[i-1] != 0 else 1
        keyword_increase += value_list_reversed[i] / divisor

    return (keyword_increase, keyword_total_sum)


'''
    recompute the set top_progression zset
        - Compute the current field progression
        - re-compute the current progression for each first 2*max_set_cardinality fields in the top_progression_zset
'''
def compute_progression(server, field_name, num_day, url_parsed):
    redis_progression_name_set = "z_top_progression_"+field_name

    keyword = url_parsed[field_name]
    if keyword is not None:

        #compute the progression of the current word
        keyword_increase, keyword_total_sum = compute_progression_word(server, num_day, keyword)

        #re-compute the progression of 2*max_set_cardinality
        current_top = server.zrevrangebyscore(redis_progression_name_set, '+inf', '-inf', withscores=True, start=0, num=2*max_set_cardinality)
        for word, value in current_top:
            word_inc, word_tot_sum = compute_progression_word(server, num_day, word)
            server.zrem(redis_progression_name_set, word)
            if (word_tot_sum > threshold_total_sum) and (word_inc > threshold_increase):
                server.zadd(redis_progression_name_set, float(word_inc), word)

        # filter before adding
        if (keyword_total_sum > threshold_total_sum) and (keyword_increase > threshold_increase):
            server.zadd(redis_progression_name_set, float(keyword_increase), keyword)



if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'WebStats'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Makes statistics about valid URL")

    # REDIS #
    r_serv_trend = redis.StrictRedis(
        host=p.config.get("ARDB_Trending", "host"),
        port=p.config.get("ARDB_Trending", "port"),
        db=p.config.get("ARDB_Trending", "db"),
        decode_responses=True)

    # FILE CURVE SECTION #
    csv_path_proto = os.path.join(os.environ['AIL_HOME'],
                                  p.config.get("Directories", "protocolstrending_csv"))
    protocolsfile_path = os.path.join(os.environ['AIL_HOME'],
                                 p.config.get("Directories", "protocolsfile"))

    csv_path_tld = os.path.join(os.environ['AIL_HOME'],
                                p.config.get("Directories", "tldstrending_csv"))
    tldsfile_path = os.path.join(os.environ['AIL_HOME'],
                                 p.config.get("Directories", "tldsfile"))

    csv_path_domain = os.path.join(os.environ['AIL_HOME'],
                                   p.config.get("Directories", "domainstrending_csv"))

    faup = Faup()
    generate_new_graph = False
    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()

        if message is None:
            if generate_new_graph:
                generate_new_graph = False
                today = datetime.date.today()
                year = today.year
                month = today.month

                print('Building protocol graph')
                lib_words.create_curve_with_word_file(r_serv_trend, csv_path_proto,
                                                      protocolsfile_path, year,
                                                      month)

                print('Building tld graph')
                lib_words.create_curve_with_word_file(r_serv_trend, csv_path_tld,
                                                      tldsfile_path, year,
                                                      month)

                print('Building domain graph')
                lib_words.create_curve_from_redis_set(r_serv_trend, csv_path_domain,
                                                      "domain", year,
                                                      month)
                print('end building')


            publisher.debug("{} queue is empty, waiting".format(config_section))
            print('sleeping')
            time.sleep(5*60)
            continue

        else:
            generate_new_graph = True
            # Do something with the message from the queue
            url, date, path = message.split()
            faup.decode(url)
            url_parsed = faup.get()

            # Scheme analysis
            analyse(r_serv_trend, 'scheme', date, url_parsed)
            # Tld analysis
            analyse(r_serv_trend, 'tld', date, url_parsed)
            # Domain analysis
            analyse(r_serv_trend, 'domain', date, url_parsed)

            compute_progression(r_serv_trend, 'scheme', num_day_to_look, url_parsed)
            compute_progression(r_serv_trend, 'tld', num_day_to_look, url_parsed)
            compute_progression(r_serv_trend, 'domain', num_day_to_look, url_parsed)

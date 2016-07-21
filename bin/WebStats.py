#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
    Template for new modules
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

    field = url_parsed[field_name]
    if field is not None:
        prev_score = server.hget(field, date)
        if prev_score is not None:
            print field + ' prev_score:' + prev_score
            server.hset(field, date, int(prev_score) + 1)
            if int(prev_score) + 1 > threshold_need_to_look:  # threshold for false possitive
                if(check_for_progression(server, field, date)):
                    to_plot.add(field)
        else:
            server.hset(field, date, 1)
            if field_name == "domain": #save domain in a set for the monthly plot
                domain_set_name = "domain_set_" + date[0:6]
                server.sadd(domain_set_name, field)
                print "added in " + domain_set_name +": "+ field

def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))
    return date_list

def compute_progression(server, field_name, num_day, url_parsed):
    redis_progression_name = 'top_progression_'+field_name
    redis_progression_name_set = 'top_progression_'+field_name+'_set'

    keyword = url_parsed[field_name]
    if keyword is not None:
        date_range = get_date_range(num_day) 
        # check if this keyword is eligible for progression
        keyword_total_sum = 0 
        value_list = []
        for date in date_range:
            curr_value = server.hget(keyword, date)
            value_list.append(int(curr_value if curr_value is not None else 0))
            keyword_total_sum += int(curr_value) if curr_value is not None else 0
        oldest_value = value_list[-1] if value_list[-1] != 0 else 1 #Avoid zero division
        keyword_increase = value_list[0] / oldest_value
        
        # filter
        if (keyword_total_sum > threshold_total_sum) and (keyword_increase > threshold_increase):
            
            if server.sismember(redis_progression_name_set, keyword): #if keyword is in the set
                server.hset(redis_progression_name, keyword, keyword_increase) #update its value

            elif (server.scard(redis_progression_name_set) < max_set_cardinality):
                    server.sadd(redis_progression_name_set, keyword)

            else: #not in the set
                #Check value for all members
                member_set = []
                for keyw in server.smembers(redis_progression_name_set):
                    member_set += (keyw, int(server.hget(redis_progression_name, keyw)))
                member_set.sort(key=lambda tup: tup[1])
                if member_set[0] < keyword_increase:
                    #remove min from set and add the new one
                    server.srem(redis_progression_name_set, member_set[0])
                    server.sadd(redis_progression_name_set, keyword)


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
    r_serv1 = redis.StrictRedis(
        host=p.config.get("Redis_Level_DB", "host"),
        port=p.config.get("Redis_Level_DB", "port"),
        db=p.config.get("Redis_Level_DB", "db"))
 
    r_serv_trend = redis.StrictRedis(
        host=p.config.get("Redis_Level_DB_Trending", "host"),
        port=p.config.get("Redis_Level_DB_Trending", "port"),
        db=p.config.get("Redis_Level_DB_Trending", "db"))

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

                print 'Building protocol graph'
                lib_words.create_curve_with_word_file(r_serv_trend, csv_path_proto,
                                                      protocolsfile_path, year,
                                                      month)

                print 'Building tld graph'
                lib_words.create_curve_with_word_file(r_serv_trend, csv_path_tld,
                                                      tldsfile_path, year,
                                                      month)

                print 'Building domain graph'
                lib_words.create_curve_from_redis_set(r_serv_trend, csv_path_domain,
                                                      "domain", year,
                                                      month)
                print 'end building'

            publisher.debug("{} queue is empty, waiting".format(config_section))
            print 'sleeping'
            time.sleep(5*60)
            continue

        else:
            generate_new_graph = True
            # Do something with the message from the queue
            url, date = message.split()
            faup.decode(url)
            url_parsed = faup.get()
            
            analyse(r_serv_trend, 'scheme', date, url_parsed)	#Scheme analysis
            analyse(r_serv_trend, 'tld', date, url_parsed)	#Tld analysis
	    analyse(r_serv_trend, 'domain', date, url_parsed)	#Domain analysis
            compute_progression(r_serv_trend, 'scheme', num_day_to_look, url_parsed)
            compute_progression(r_serv_trend, 'tld', num_day_to_look, url_parsed)
            compute_progression(r_serv_trend, 'domain', num_day_to_look, url_parsed)

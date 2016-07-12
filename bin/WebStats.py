#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
    Template for new modules
"""

import time
import datetime
import re
import redis
import os
from packages import lib_words
from packages.Date import Date
from pubsublogger import publisher
from packages import Paste
from Helper import Process
from pyfaup.faup import Faup

# Config Var
threshold_need_to_look	= 50
range_to_look		= 10
threshold_to_plot	= 1 #500%
to_plot			= set() 
clean_frequency		= 10 #minutes

def analyse(server, field_name):
    field = url_parsed[field_name]
    if field is not None:
        prev_score = server.hget(field, date)
        if prev_score is not None:
            server.hset(field, date, int(prev_score) + 1)
        else:
            server.hset(field, date, 1)

def analyse_and_progression(server, field_name):
    field = url_parsed[field_name]
    if field is not None:
        prev_score = server.hget(field, date)
        if prev_score is not None:
            print field + ' prev_score:' + prev_score
            server.hset(field, date, int(prev_score) + 1)
            if int(prev_score) + 1 > threshold_need_to_look: #threshold for false possitive
                if(check_for_progression(server, field, date)):
                    to_plot.add(field)
        else:
            server.hset(field, date, 1)

def check_for_progression(server, field, date):
    previous_data = set()
    tot_sum = 0
    for i in range(0, range_to_look):
        curr_value = server.hget(field, Date(date).substract_day(i))
        if curr_value is None: #no further data
            break
        else:
            curr_value = int(curr_value)
            previous_data.add(curr_value)
            tot_sum += curr_value 
            if i == 0:
                today_val = curr_value

   
    print 'totsum='+str(tot_sum)
    print 'div='+str(tot_sum/today_val)
    if tot_sum/today_val >= threshold_to_plot:
        return True
    else:
        return False

def clean_to_plot():
    temp_to_plot = set()
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month)+str(curr_date.day))

    for elem in to_plot:
        if(check_for_progression(field, date)):
            temp_to_plot.add(elem)    
    to_plot = temp_to_plot

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
 
    r_serv2 = redis.StrictRedis(
        host=p.config.get("Redis_Level_DB_Domain", "host"),
        port=p.config.get("Redis_Level_DB_Domain", "port"),
        db=p.config.get("Redis_Level_DB_Domain", "db"))

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
                print 'Building graph'
                today = datetime.date.today()
                year = today.year
                month = today.month

                lib_words.create_curve_with_word_file(r_serv1, csv_path_proto,
                                                      protocolsfile_path, year,
                                                      month)

                lib_words.create_curve_with_word_file(r_serv1, csv_path_tld,
                                                      tldsfile_path, year,
                                                      month)

                lib_words.create_curve_with_list(r_serv2, csv_path_domain,
                                                      to_plot, year,
                                                      month)
                print 'end building'

            publisher.debug("{} queue is empty, waiting".format(config_section))
            print 'sleeping'
            time.sleep(5)
            continue

	else:
            generate_new_graph = True
            # Do something with the message from the queue
            url, date = message.split()
            faup.decode(url)
            url_parsed = faup.get()
            
            analyse(r_serv1, 'scheme')	#Scheme analysis
            analyse(r_serv1, 'tld')	#Tld analysis
	    analyse_and_progression(r_serv2, 'domain')	#Domain analysis

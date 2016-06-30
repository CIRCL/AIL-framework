#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
    Template for new modules
"""

import time
import re
import redis
import os
from pubsublogger import publisher
from packages import Paste
from Helper import Process



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

    # FILE CURVE SECTION #
    csv_path = os.path.join(os.environ['AIL_HOME'],
                            p.config.get("Directories", "protocolstrending_csv"))
    protocolsfile_path = os.path.join(os.environ['AIL_HOME'],
                                 p.config.get("Directories", "protocolsfile"))

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        generate_new_graph = False
        
        if message is None:
            if generate_new_graph:
                generate_new_graph = False
                print 'Building graph'
                today = datetime.date.today()
                year = today.year
                month = today.month
                lib_words.create_curve_with_word_file(r_serv1, csv_path,
                                                      protocolsfile_path, year,
                                                      month)

            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

	else:
            generate_new_graph = True
            # Do something with the message from the queue
	    scheme, credential, subdomain, domain, host, tld, \
                port, resource_path, query_string, f1, f2, f3, \
                f4 , date= message.split()
                
            prev_score = r_serv1.hget(scheme, date)
            if prev_score is not None:
                r_serv1.hset(scheme, date, int(prev_score) + int(score))
            else:
                r_serv1.hset(scheme, date, score)



















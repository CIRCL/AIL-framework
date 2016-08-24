#!/usr/bin/env python2
# -*-coding:UTF-8 -*


import time
import datetime
import calendar
import redis
import os
import ConfigParser
import json
from prettytable import PrettyTable

# CONFIG VARIABLES
threshold_stucked_module = 60*60*1 #1 hour
log_filename = "../logs/moduleInfo.log"



if __name__ == "__main__":

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    
    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)

    # REDIS #
    server = redis.StrictRedis(
        host=cfg.get("Redis_Queues", "host"),
        port=cfg.getint("Redis_Queues", "port"),
        db=cfg.getint("Redis_Queues", "db"))

    while True:

        table1 = PrettyTable(['#', 'Queue', 'Amount', 'Paste start time', 'Processing time for current paste (H:M:S)', 'Paste hash'], sortby="Processing time for current paste (H:M:S)", reversesort=True)
        table2 = PrettyTable(['#', 'Queue', 'Amount', 'Paste start time', 'Time since idle (H:M:S)', 'Last paste hash'], sortby="Time since idle (H:M:S)", reversesort=True)
        num = 0
        for queue, card in server.hgetall("queues").iteritems():
            key = "MODULE_" + queue
            value = server.get(key)
            if value is not None:
                timestamp, path = value.split(", ")
                if timestamp is not None and path is not None:
                    num += 1
                    startTime_readable = datetime.datetime.fromtimestamp(int(timestamp))
                    processed_time_readable = str((datetime.datetime.now() - startTime_readable)).split('.')[0]

                    if int((datetime.datetime.now() - startTime_readable).total_seconds()) > threshold_stucked_module:
                        log = open(log_filename, 'a')
                        log.write(json.dumps([queue, card, str(startTime_readable), str(processed_time_readable), path]) + "\n")

                    if int(card) > 0:
                        table1.add_row([num, queue, card, startTime_readable, processed_time_readable, path])
                    else:
                        table2.add_row([num, queue, card, startTime_readable, processed_time_readable, path])

        os.system('clear') 
        print 'Working queues:\n'
        print table1
        print '\n'
        print 'Ideling queues:\n'
        print table2
        time.sleep(5)

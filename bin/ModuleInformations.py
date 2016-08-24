#!/usr/bin/env python2
# -*-coding:UTF-8 -*


import time
import datetime
import calendar
import redis
import os
import ConfigParser
from prettytable import PrettyTable

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

        table = PrettyTable(['#', 'Queue', 'Amount', 'Paste start time', 'Processing time for current paste (H:M:S)', 'Paste hash'], sortby="Processing time for current paste (H:M:S)", reversesort=True)
        num = 0
        for queue, card in server.hgetall("queues").iteritems():
            key = "MODULE_" + queue
            value = server.get(key)
            if value is not None:
                timestamp, path = value.split(", ")
                if timestamp is not None and path is not None:
                    num += 1
                    startTime_readable = datetime.datetime.utcfromtimestamp(int(timestamp))
                    processed_time_readable = str((datetime.datetime.now() - startTime_readable)).split('.')[0]
                    table.add_row([num, queue, card, startTime_readable, processed_time_readable, path])

        os.system('clear') 
        print table
        time.sleep(1)

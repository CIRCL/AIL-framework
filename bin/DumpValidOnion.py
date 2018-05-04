#!/usr/bin/env python3
# -*-coding:UTF-8 -*

from pubsublogger import publisher
from Helper import Process
import datetime
import time

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'DumpValidOnion'
    dump_file = 'dump.out'

    p = Process(config_section)

    # FUNCTIONS #
    publisher.info("Script subscribed to channel ValidOnion")

    while True:
        message = p.get_from_set()
        if message is not None:
            f = open(dump_file, 'a')
            while message is not None:
                print(message)
                date = datetime.datetime.now()
                if message is not None:
                    f.write(date.isoformat() + ' ' + message + '\n')
                else:
                    break
                message = p.get_from_set()
            f.close()
        else:
            time.sleep(20)

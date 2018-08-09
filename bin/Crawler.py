#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis
import datetime
import time
import subprocess

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process
from pubsublogger import publisher


def signal_handler(sig, frame):
    sys.exit(0)

if __name__ == '__main__':

    publisher.port = 6380
    publisher.channel = "Script"

    publisher.info("Script Crawler started")

    config_section = 'Crawler'

    # Setup the I/O queues
    p = Process(config_section)

    splash_url = p.config.get("Crawler", "splash_url")
    http_proxy = p.config.get("Crawler", "http_proxy")
    crawler_depth_limit = p.config.getint("Crawler", "crawler_depth_limit")

    #signal.signal(signal.SIGINT, signal_handler)

    r_serv_metadata = redis.StrictRedis(
        host=p.config.get("ARDB_Metadata", "host"),
        port=p.config.getint("ARDB_Metadata", "port"),
        db=p.config.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    r_cache = redis.StrictRedis(
        host=p.config.get("Redis_Cache", "host"),
        port=p.config.getint("Redis_Cache", "port"),
        db=p.config.getint("Redis_Cache", "db"),
        decode_responses=True)

    r_onion = redis.StrictRedis(
        host=p.config.get("ARDB_Onion", "host"),
        port=p.config.getint("ARDB_Onion", "port"),
        db=p.config.getint("ARDB_Onion", "db"),
        decode_responses=True)

    while True:

        message = p.get_from_set()
        # Recovering the streamed message informations.
        if message is not None:
            splitted = message.split(';')
            if len(splitted) == 2:
                url, paste = splitted

                print(url)

                if not r_cache.exists(url):
                    super_father = r_serv_metadata.hget('paste_metadata:'+paste, 'super_father')
                    if super_father is None:
                        super_father=paste

                    process = subprocess.Popen(["python", './torcrawler/tor_crawler.py', url, paste, super_father],
                                               stdout=subprocess.PIPE)
                    while process.poll() is None:
                        time.sleep(1)

                    date = datetime.datetime.now().strftime("%Y%m%d")
                    print(date)
                    url_domain = url.replace('http://', '')
                    if process.returncode == 0:
                        if r_serv_metadata.exists('paste_children:'+paste):
                            msg = 'infoleak:automatic-detection="onion";{}'.format(paste)
                            p.populate_set_out(msg, 'Tags')

                        r_onion.sadd('onion_up:'+date , url_domain)
                    else:
                        r_onion.sadd('onion_down:'+date , url_domain)
                        print(process.stdout.read())

            else:
                continue
        else:
            time.sleep(1)

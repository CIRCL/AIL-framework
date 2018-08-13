#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import re
import redis
import datetime
import time
import subprocess

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process
from pubsublogger import publisher


def signal_handler(sig, frame):
    sys.exit(0)

def crawl_onion(url, domain):
    date = datetime.datetime.now().strftime("%Y%m%d")

    if not r_onion.sismember('onion_up:'+date , domain):
        super_father = r_serv_metadata.hget('paste_metadata:'+paste, 'super_father')
        if super_father is None:
            super_father=paste

        process = subprocess.Popen(["python", './torcrawler/tor_crawler.py', url, domain, paste, super_father],
                                   stdout=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(1)

        if process.returncode == 0:
            if r_serv_metadata.exists('paste_children:'+paste):
                msg = 'infoleak:automatic-detection="onion";{}'.format(paste)
                p.populate_set_out(msg, 'Tags')
            print(process.stdout.read())

            r_onion.sadd('onion_up:'+date , domain)
            r_onion.sadd('onion_up_link:'+date , url)
        else:
            r_onion.sadd('onion_down:'+date , domain)
            r_onion.sadd('onion_down_link:'+date , url)
            print(process.stdout.read())


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

    url_regex = "((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.onion)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
    re.compile(url_regex)

    while True:

        message = p.get_from_set()
        # Recovering the streamed message informations.
        if message is not None:
            splitted = message.split(';')
            if len(splitted) == 2:
                url, paste = splitted

                url_list = re.findall(url_regex, url)[0]
                if url_list[1] == '':
                    url= 'http://{}'.format(url)

                link, s, credential, subdomain, domain, host, port, \
                    resource_path, query_string, f1, f2, f3, f4 = url_list
                domain = url_list[4]

                domain_url = 'http://{}'.format(domain)

                print('------------------START ONIOM CRAWLER------------------')
                print('url:         {}'.format(url))
                print('domain:      {}'.format(domain))
                print('domain_url:  {}'.format(domain_url))

                crawl_onion(url, domain)
                if url != domain_url:
                    crawl_onion(domain_url, domain)

            else:
                continue
        else:
            time.sleep(1)

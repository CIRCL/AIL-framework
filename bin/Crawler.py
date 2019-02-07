#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import re
import redis
import datetime
import time
import subprocess
import requests

from pyfaup.faup import Faup

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process
from pubsublogger import publisher

# ======== GLOBAL VARIABLES ========
publisher.port = 6380
publisher.channel = "Script"

config_section = 'Crawler'

# Setup the I/O queues
p = Process(config_section)

accepted_services = ['onion', 'regular']

dic_regex = {}
dic_regex['onion'] = "((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.onion)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
re.compile(dic_regex['onion'])
dic_regex['i2p'] = "((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.i2p)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
re.compile(dic_regex['i2p'])
dic_regex['regular'] = dic_regex['i2p']

faup = Faup()

PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], p.config.get("Directories", "pastes"))

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

# ======== FUNCTIONS ========
def decode_val(value):
    if value is not None:
        value = value.decode()
    return value

def load_type_blacklist(type_service):
    # load domains blacklist
    try:
        with open(os.path.join(os.environ['AIL_BIN'],'/torcrawler/blacklist_{}.txt'.format(type_service)), 'r') as f:
            # # TODO: # FIXME:  remove this
            r_onion.delete('blacklist_{}'.format(type_service))
            lines = f.read().splitlines()
            for line in lines:
                r_onion.sadd('blacklist_{}'.format(type_service), line)
    except Exception:
        pass


def on_error_send_message_back_in_queue(type_hidden_service, domain, message):
    # send this msg back in the queue
    if not r_onion.sismember('{}_domain_crawler_queue'.format(type_hidden_service), domain):
        r_onion.sadd('{}_domain_crawler_queue'.format(type_hidden_service), domain)
        r_onion.sadd('{}_crawler_priority_queue'.format(type_hidden_service), message)

def crawl_onion(url, domain, date, date_month, message):

    r_cache.hset('metadata_crawler:{}'.format(splash_port), 'crawling_domain', domain)
    r_cache.hset('metadata_crawler:{}'.format(splash_port), 'started_time', datetime.datetime.now().strftime("%Y/%m/%d  -  %H:%M.%S"))

    #if not r_onion.sismember('full_onion_up', domain) and not r_onion.sismember('onion_down:'+date , domain):
    super_father = r_serv_metadata.hget('paste_metadata:'+paste, 'super_father')
    if super_father is None:
        super_father=paste

    retry = True
    nb_retry = 0
    while retry:
        try:
            r = requests.get(splash_url , timeout=30.0)
            retry = False
        except Exception:
            # TODO: relaunch docker or send error message
            nb_retry += 1

            if nb_retry == 6:
                on_error_send_message_back_in_queue(type_hidden_service, domain, message)
                publisher.error('{} SPASH DOWN'.format(splash_url))
                print('--------------------------------------')
                print('         \033[91m DOCKER SPLASH DOWN\033[0m')
                print('          {} DOWN'.format(splash_url))
                r_cache.hset('metadata_crawler:{}'.format(splash_port), 'status', 'SPLASH DOWN')
                nb_retry == 0

            print('         \033[91m DOCKER SPLASH NOT AVAILABLE\033[0m')
            print('          Retry({}) in 10 seconds'.format(nb_retry))
            time.sleep(10)

    if r.status_code == 200:
        r_cache.hset('metadata_crawler:{}'.format(splash_port), 'status', 'Crawling')
        process = subprocess.Popen(["python", './torcrawler/tor_crawler.py', splash_url, type_hidden_service, url, domain, paste, super_father],
                                   stdout=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(1)

        if process.returncode == 0:
            output = process.stdout.read().decode()
            print(output)
            # error: splash:Connection to proxy refused
            if 'Connection to proxy refused' in output:
                on_error_send_message_back_in_queue(type_hidden_service, domain, message)
                publisher.error('{} SPASH, PROXY DOWN OR BAD CONFIGURATION'.format(splash_url))
                print('------------------------------------------------------------------------')
                print('         \033[91m SPLASH: Connection to proxy refused')
                print('')
                print('            PROXY DOWN OR BAD CONFIGURATION\033[0m'.format(splash_url))
                print('------------------------------------------------------------------------')
                r_cache.hset('metadata_crawler:{}'.format(splash_port), 'status', 'Error')
                exit(-2)
        else:
            print(process.stdout.read())
            exit(-1)
    else:
        on_error_send_message_back_in_queue(type_hidden_service, domain, message)
        print('--------------------------------------')
        print('         \033[91m DOCKER SPLASH DOWN\033[0m')
        print('          {} DOWN'.format(splash_url))
        r_cache.hset('metadata_crawler:{}'.format(splash_port), 'status', 'Crawling')
        exit(1)

# ======== MAIN ========
if __name__ == '__main__':

    if len(sys.argv) != 3:
        #print('usage:', 'Crawler.py', 'type_hidden_service (onion or i2p or regular)', 'splash_port')
        print('usage:', 'Crawler.py', 'mode (manual or automatic)', 'splash_port')
        exit(1)

    mode = sys.argv[1]
    splash_port = sys.argv[2]

    if mode == 'automatic':
        type_hidden_service = 'onion'

    # verify crawler type (type_hidden_service)
    if type_hidden_service not in accepted_services:
        print('incorrect crawler type: {}'.format(type_hidden_service))
        exit(0)
    else:
        publisher.info("Script Crawler started")

    # load domains blacklist
    load_type_blacklist(type_hidden_service)

    splash_url = '{}:{}'.format( p.config.get("Crawler", "splash_url_onion"),  splash_port)
    print('splash url: {}'.format(splash_url))

    crawler_depth_limit = p.config.getint("Crawler", "crawler_depth_limit")

    # Crawler status
    r_cache.sadd('all_crawler:{}'.format(type_hidden_service), splash_port)
    r_cache.hset('metadata_crawler:{}'.format(splash_port), 'status', 'Waiting')
    r_cache.hset('metadata_crawler:{}'.format(splash_port), 'started_time', datetime.datetime.now().strftime("%Y/%m/%d  -  %H:%M.%S"))


    while True:

        if mode == 'automatic':
            # Priority Queue - Recovering the streamed message informations.
            message = r_onion.spop('{}_crawler_priority_queue'.format(type_hidden_service))

            if message is None:
                # Recovering the streamed message informations.
                message = r_onion.spop('{}_crawler_queue'.format(type_hidden_service))
        else:
            pass

        if message is not None:

            splitted = message.split(';')
            if len(splitted) == 2:
                url, paste = splitted
                paste = paste.replace(PASTES_FOLDER+'/', '')

                # extract data from url
                faup.decode(url)
                url_unpack = faup.get()
                url = decode_val(url_unpack['url'])
                port = decode_val(url_unpack['port'])
                scheme = decode_val(url_unpack['scheme'])
                domain = decode_val(url_unpack['domain'])
                host = decode_val(url_unpack['domain'])

                # Add Scheme to url
                if scheme is None:
                    url= 'http://{}'.format(url)
                domain_url = 'http://{}'.format(domain)


                # remove url to crawl from queue
                r_onion.srem('{}_domain_crawler_queue'.format(type_hidden_service), domain)

                print()
                print()
                print('\033[92m------------------START CRAWLER------------------\033[0m')
                print('crawler type:     {}'.format(type_hidden_service))
                print('\033[92m-------------------------------------------------\033[0m')
                print('url:         {}'.format(url))
                print('domain:      {}'.format(domain))
                print('domain_url:  {}'.format(domain_url))

                if not r_onion.sismember('blacklist_{}'.format(type_hidden_service), domain):

                    date = datetime.datetime.now().strftime("%Y%m%d")
                    date_month = datetime.datetime.now().strftime("%Y%m")

                    if not r_onion.sismember('month_{}_up:{}'.format(type_hidden_service, date_month), domain) and not r_onion.sismember('{}_down:{}'.format(type_hidden_service, date), domain):
                        # first seen
                        if not r_onion.hexists('{}_metadata:{}'.format(type_hidden_service, domain), 'first_seen'):
                            r_onion.hset('{}_metadata:{}'.format(type_hidden_service, domain), 'first_seen', date)

                        # last_father
                        r_onion.hset('{}_metadata:{}'.format(type_hidden_service, domain), 'paste_parent', paste)

                        # last check
                        r_onion.hset('{}_metadata:{}'.format(type_hidden_service, domain), 'last_check', date)

                        # Launch Scrapy-Splash Crawler
                        crawl_onion(url, domain, date, date_month, message)
                        # Crawl Domain
                        if url != domain_url:
                            #Crawl Domain with port number
                            if port is not None:
                                print('{}:{}'.format(domain_url, port))
                                crawl_onion('{}:{}'.format(domain_url, port), domain, date, date_month, message)
                            #Crawl without port number
                            print(domain_url)
                            crawl_onion(domain_url, domain, date, date_month, message)

                        # update last check
                        r_onion.hset('{}_metadata:{}'.format(type_hidden_service, domain), 'last_check', date)

                        # save down onion
                        if not r_onion.sismember('{}_up:{}'.format(type_hidden_service, date), domain):
                            r_onion.sadd('{}_down:{}'.format(type_hidden_service, date), domain)
                        else:
                            #r_onion.hincrby('{}_link_up'.format(type_hidden_service), url, 1)
                            if r_onion.sismember('month_{}_up:{}'.format(type_hidden_service, date_month), domain) and r_serv_metadata.exists('paste_children:'+paste):
                                msg = 'infoleak:automatic-detection="{}";{}'.format(type_hidden_service, paste)
                                p.populate_set_out(msg, 'Tags')

                        # add onion screenshot history
                            # add crawled days
                        if r_onion.lindex('{}_history:{}'.format(type_hidden_service, domain), 0) != date:
                            r_onion.lpush('{}_history:{}'.format(type_hidden_service, domain), date)
                            # add crawled history by date
                        r_onion.lpush('{}_history:{}:{}'.format(type_hidden_service, domain, date), paste)

                        if mode == 'automatic':
                            # check external onions links (full_crawl)
                            external_domains = set()
                            for link in r_onion.smembers('domain_{}_external_links:{}'.format(type_hidden_service, domain)):
                                external_domain = re.findall(dic_regex[type_hidden_service], link)
                                external_domain.extend(re.findall(url_i2p, link))
                                if len(external_domain) > 0:
                                    external_domain = external_domain[0][4]
                                else:
                                    continue
                                if '.onion' in external_domain and external_domain != domain:
                                    external_domains.add(external_domain)
                                elif '.i2p' in external_domain and external_domain != domain:
                                    external_domains.add(external_domain)
                            if len(external_domains) >= 10:
                                r_onion.sadd('{}_potential_source'.format(type_hidden_service), domain)
                            r_onion.delete('domain_{}_external_links:{}'.format(type_hidden_service, domain))
                            print(r_onion.smembers('domain_{}_external_links:{}'.format(type_hidden_service, domain)))

                        # update list, last crawled sites
                        r_onion.lpush('last_{}'.format(type_hidden_service), domain)
                        r_onion.ltrim('last_{}'.format(type_hidden_service), 0, 15)

                        #update crawler status
                        r_cache.hset('metadata_crawler:{}'.format(splash_port), 'status', 'Waiting')
                        r_cache.hdel('metadata_crawler:{}'.format(splash_port), 'crawling_domain')
                else:
                    print('                 Blacklisted Site')
                    print()
                    print()

            else:
                continue
        else:
            time.sleep(1)

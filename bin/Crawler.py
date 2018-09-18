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

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process
from pubsublogger import publisher


def signal_handler(sig, frame):
    sys.exit(0)

def crawl_onion(url, domain, date, date_month):

    #if not r_onion.sismember('full_onion_up', domain) and not r_onion.sismember('onion_down:'+date , domain):
    super_father = r_serv_metadata.hget('paste_metadata:'+paste, 'super_father')
    if super_father is None:
        super_father=paste

    try:
        r = requests.get(splash_url , timeout=30.0)
    except Exception:
        ## FIXME: # TODO: relaunch docker or send error message
        print('--------------------------------------')
        print('          DOCKER SPLASH DOWN')
        exit(0)

    if r.status_code == 200:
        process = subprocess.Popen(["python", './torcrawler/tor_crawler.py', splash_url, http_proxy, type_hidden_service, url, domain, paste, super_father],
                                   stdout=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(1)

        if process.returncode == 0:
            if r_serv_metadata.exists('paste_children:'+paste):
                msg = 'infoleak:automatic-detection="{}";{}'.format(type_hidden_service, paste)
                p.populate_set_out(msg, 'Tags')

            print(process.stdout.read())

        else:
            print(process.stdout.read())
            exit(0)
    else:
        ## FIXME: # TODO: relaunch docker
        exit(0)


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('usage:', 'Crawler.py', 'type_hidden_service (onion or i2p or regular)')
        exit(1)

    type_hidden_service = sys.argv[1]

    publisher.port = 6380
    publisher.channel = "Script"

    publisher.info("Script Crawler started")

    config_section = 'Crawler'

    # Setup the I/O queues
    p = Process(config_section)

    url_onion = "((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.onion)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
    re.compile(url_onion)
    url_i2p = "((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.i2p)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
    re.compile(url_i2p)

    if type_hidden_service == 'onion':
        regex_hidden_service = url_onion
        splash_url = p.config.get("Crawler", "splash_url_onion")
        http_proxy = p.config.get("Crawler", "http_proxy_onion")
    elif type_hidden_service == 'i2p':
        regex_hidden_service = url_i2p
        splash_url = p.config.get("Crawler", "splash_url_i2p")
        http_proxy = p.config.get("Crawler", "http_proxy_i2p")
    elif type_hidden_service == 'regular':
        regex_hidden_service = url_i2p
        splash_url = p.config.get("Crawler", "splash_url_onion")
        http_proxy = p.config.get("Crawler", "http_proxy_onion")
    else:
        print('incorrect crawler type: {}'.format(type_hidden_service))
        exit(0)

    print(type_hidden_service)

    crawler_depth_limit = p.config.getint("Crawler", "crawler_depth_limit")

    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], p.config.get("Directories", "pastes"))

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

        # Recovering the streamed message informations. http://eepsites.i2p
        message = r_onion.spop('{}_crawler_queue'.format(type_hidden_service))
        #message = 'http://i2pwiki.i2p;test'
        #message = 'http://i2host.i2p;test'

        # # FIXME: remove
        if message is None:
            print('get ardb message')
            message = r_onion.spop('mess_onion')

        if message is not None:
            print(message)

            splitted = message.split(';')
            if len(splitted) == 2:
                url, paste = splitted
                paste = paste.replace(PASTES_FOLDER+'/', '')
                print(paste)
                '''
                if not '.onion' in url:
                    print('not onion')
                    continue
                '''


                url_list = re.findall(regex_hidden_service, url)[0]
                if url_list[1] == '':
                    url= 'http://{}'.format(url)

                link, s, credential, subdomain, domain, host, port, \
                    resource_path, query_string, f1, f2, f3, f4 = url_list
                domain = url_list[4]
                r_onion.srem('{}_domain_crawler_queue'.format(type_hidden_service), domain)

                domain_url = 'http://{}'.format(domain)

                print('------------------START CRAWLER------------------')
                print(type_hidden_service)
                print('-------------------------------------------------')
                print('url:         {}'.format(url))
                print('domain:      {}'.format(domain))
                print('domain_url:  {}'.format(domain_url))

                if not r_onion.sismember('banned_{}'.format(type_hidden_service), domain):

                    date = datetime.datetime.now().strftime("%Y%m%d")
                    date_month = datetime.datetime.now().strftime("%Y%m")

                    if not r_onion.sismember('month_{}_up:{}'.format(type_hidden_service, date_month), domain) and not r_onion.sismember('{}_down:{}'.format(type_hidden_service, date), domain):

                        crawl_onion(url, domain, date, date_month)
                        if url != domain_url:
                            print(url)
                            print(domain_url)
                            crawl_onion(domain_url, domain, date, date_month)

                        # save down onion
                        if not r_onion.sismember('{}_up:{}'.format(type_hidden_service, date), domain):
                            r_onion.sadd('{}_down:{}'.format(type_hidden_service, date), domain)
                            r_onion.sadd('{}_down_link:{}'.format(type_hidden_service, date), url)
                            r_onion.hincrby('{}_link_down'.format(type_hidden_service), url, 1)
                            if not r_onion.exists('{}_metadata:{}'.format(type_hidden_service, domain)):
                                r_onion.hset('{}_metadata:{}'.format(type_hidden_service, domain), 'first_seen', date)
                            r_onion.hset('{}_metadata:{}'.format(type_hidden_service,domain), 'last_seen', date)
                        else:
                            r_onion.hincrby('{}_link_up'.format(type_hidden_service), url, 1)

                        # last check
                        r_onion.hset('{}_metadata:{}'.format(type_hidden_service, domain), 'last_check', date)

                        # last_father
                        r_onion.hset('{}_metadata:{}'.format(type_hidden_service, domain), 'paste_parent', paste)

                        # add onion screenshot history
                            # add crawled days
                        if r_onion.lindex('{}_history:{}'.format(type_hidden_service, domain), 0) != date:
                            r_onion.lpush('{}_history:{}'.format(type_hidden_service, domain), date)
                            # add crawled history by date
                        r_onion.lpush('{}_history:{}:{}'.format(type_hidden_service, domain, date), paste) #add datetime here


                        # check external onions links (full_scrawl)
                        external_domains = set()
                        for link in r_onion.smembers('domain_{}_external_links:{}'.format(type_hidden_service, domain)):
                            external_domain = re.findall(url_onion, link)
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

                        r_onion.lpush('last_{}'.format(type_hidden_service), domain)
                        r_onion.ltrim('last_{}'.format(type_hidden_service), 0, 15)

                        #send all crawled domain past
                        msg = domain
                        p.populate_set_out(msg, 'DomainSubject')

                        #time.sleep(30)

            else:
                continue
        else:
            time.sleep(1)

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import re
import uuid
import json
import redis
import datetime
import time
import subprocess
import requests

from collections import deque
from pyfaup.faup import Faup

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process
from pubsublogger import publisher

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import crawlers

# ======== FUNCTIONS ========

def load_blacklist(service_type):
    try:
        with open(os.environ['AIL_BIN']+'/torcrawler/blacklist_{}.txt'.format(service_type), 'r') as f:
            redis_crawler.delete('blacklist_{}'.format(service_type))
            lines = f.read().splitlines()
            for line in lines:
                redis_crawler.sadd('blacklist_{}'.format(service_type), line)
    except Exception:
        pass

def update_auto_crawler():
    current_epoch = int(time.time())
    list_to_crawl = redis_crawler.zrangebyscore('crawler_auto_queue', '-inf', current_epoch)
    for elem_to_crawl in list_to_crawl:
        mess, type = elem_to_crawl.rsplit(';', 1)
        redis_crawler.sadd('{}_crawler_priority_queue'.format(type), mess)
        redis_crawler.zrem('crawler_auto_queue', elem_to_crawl)

# Extract info form url (url, domain, domain url, ...)
def unpack_url(url):
    to_crawl = {}
    faup.decode(url)
    url_unpack = faup.get()
    # # FIXME: # TODO: remove me
    try:
        to_crawl['domain'] = url_unpack['domain'].decode()
    except:
        to_crawl['domain'] = url_unpack['domain']
    to_crawl['domain'] = to_crawl['domain'].lower()


    # force lower case domain/subdomain (rfc4343)
    # # FIXME: # TODO: remove me
    try:
        url_host = url_unpack['host'].decode()
    except:
        url_host = url_unpack['host']

    new_url_host = url_host.lower()
    url_lower_case = url.replace(url_host, new_url_host, 1)

    if url_unpack['scheme'] is None:
        to_crawl['scheme'] = 'http'
        url= 'http://{}'.format(url_lower_case)
    else:
        # # FIXME: # TODO: remove me
        try:
            scheme = url_unpack['scheme'].decode()
        except Exception as e:
            scheme = url_unpack['scheme']
        if scheme in default_proto_map:
            to_crawl['scheme'] = scheme
            url = url_lower_case
        else:
            redis_crawler.sadd('new_proto', '{} {}'.format(scheme, url_lower_case))
            to_crawl['scheme'] = 'http'
            url= 'http://{}'.format(url_lower_case.replace(scheme, '', 1))

    if url_unpack['port'] is None:
        to_crawl['port'] = default_proto_map[to_crawl['scheme']]
    else:
        # # FIXME: # TODO: remove me
        try:
            port = url_unpack['port'].decode()
        except:
            port = url_unpack['port']
        # Verify port number                        #################### make function to verify/correct port number
        try:
            int(port)
        # Invalid port Number
        except Exception as e:
            port = default_proto_map[to_crawl['scheme']]
        to_crawl['port'] = port

    #if url_unpack['query_string'] is None:
    #    if to_crawl['port'] == 80:
    #        to_crawl['url']= '{}://{}'.format(to_crawl['scheme'], url_unpack['host'].decode())
    #    else:
    #        to_crawl['url']= '{}://{}:{}'.format(to_crawl['scheme'], url_unpack['host'].decode(), to_crawl['port'])
    #else:
    #    to_crawl['url']= '{}://{}:{}{}'.format(to_crawl['scheme'], url_unpack['host'].decode(), to_crawl['port'], url_unpack['query_string'].decode())

    to_crawl['url'] = url
    if to_crawl['port'] == 80:
        to_crawl['domain_url'] = '{}://{}'.format(to_crawl['scheme'], new_url_host)
    else:
        to_crawl['domain_url'] = '{}://{}:{}'.format(to_crawl['scheme'], new_url_host, to_crawl['port'])

    # # FIXME: # TODO: remove me
    try:
        to_crawl['tld'] = url_unpack['tld'].decode()
    except:
        to_crawl['tld'] = url_unpack['tld']

    return to_crawl

def get_crawler_config(redis_server, mode, service_type, domain, url=None):
    crawler_options = {}
    if mode=='auto':
        config = redis_server.get('crawler_config:{}:{}:{}:{}'.format(mode, service_type, domain, url))
    else:
        config = redis_server.get('crawler_config:{}:{}:{}'.format(mode, service_type, domain))
    if config is None:
        config = {}
    else:
        config = json.loads(config)
    for option in default_crawler_config:
        if option in config:
            crawler_options[option] = config[option]
        else:
            crawler_options[option] = default_crawler_config[option]
    if mode == 'auto':
        crawler_options['time'] = int(config['time'])
    elif mode == 'manual':
        redis_server.delete('crawler_config:{}:{}:{}'.format(mode, service_type, domain))
    return crawler_options

def load_crawler_config(queue_type, service_type, domain, paste, url, date):
    crawler_config = {}
    crawler_config['splash_url'] = f'http://{splash_url}'
    crawler_config['item'] = paste
    crawler_config['service_type'] = service_type
    crawler_config['domain'] = domain
    crawler_config['date'] = date

    if queue_type and queue_type != 'tor':
        service_type = queue_type

    # Auto and Manual Crawling
    # Auto ################################################# create new entry, next crawling => here or when ended ?
    if paste == 'auto':
        crawler_config['crawler_options'] = get_crawler_config(redis_crawler, 'auto', service_type, domain, url=url)
        crawler_config['requested'] = True
    # Manual
    elif paste == 'manual':
        crawler_config['crawler_options'] = get_crawler_config(r_cache, 'manual', service_type, domain)
        crawler_config['requested'] = True
    # default crawler
    else:
        crawler_config['crawler_options'] = get_crawler_config(redis_crawler, 'default', service_type, domain)
        crawler_config['requested'] = False
    return crawler_config

def is_domain_up_day(domain, type_service, date_day):
    if redis_crawler.sismember('{}_up:{}'.format(type_service, date_day), domain):
        return True
    else:
        return False

def set_crawled_domain_metadata(type_service, date, domain, father_item):
    # first seen
    if not redis_crawler.hexists('{}_metadata:{}'.format(type_service, domain), 'first_seen'):
        redis_crawler.hset('{}_metadata:{}'.format(type_service, domain), 'first_seen', date['date_day'])

    redis_crawler.hset('{}_metadata:{}'.format(type_service, domain), 'paste_parent', father_item)
    # last check
    redis_crawler.hset('{}_metadata:{}'.format(type_service, domain), 'last_check', date['date_day'])

# Put message back on queue
def on_error_send_message_back_in_queue(type_service, domain, message):
    if not redis_crawler.sismember('{}_domain_crawler_queue'.format(type_service), domain):
        redis_crawler.sadd('{}_domain_crawler_queue'.format(type_service), domain)
        redis_crawler.sadd('{}_crawler_priority_queue'.format(type_service), message)

def crawl_onion(url, domain, port, type_service, message, crawler_config):
    crawler_config['url'] = url
    crawler_config['port'] = port
    print('Launching Crawler: {}'.format(url))

    r_cache.hset('metadata_crawler:{}'.format(splash_url), 'crawling_domain', domain)
    r_cache.hset('metadata_crawler:{}'.format(splash_url), 'started_time', datetime.datetime.now().strftime("%Y/%m/%d  -  %H:%M.%S"))

    retry = True
    nb_retry = 0
    while retry:
        try:
            r = requests.get(f'http://{splash_url}' , timeout=30.0)
            retry = False
        except Exception:
            # TODO: relaunch docker or send error message
            nb_retry += 1

            if nb_retry == 2:
                crawlers.restart_splash_docker(splash_url, splash_name)
                time.sleep(20)

            if nb_retry == 6:
                on_error_send_message_back_in_queue(type_service, domain, message)
                publisher.error('{} SPASH DOWN'.format(splash_url))
                print('--------------------------------------')
                print('         \033[91m DOCKER SPLASH DOWN\033[0m')
                print('          {} DOWN'.format(splash_url))
                r_cache.hset('metadata_crawler:{}'.format(splash_url), 'status', 'SPLASH DOWN')
                nb_retry == 0

            print('         \033[91m DOCKER SPLASH NOT AVAILABLE\033[0m')
            print('          Retry({}) in 10 seconds'.format(nb_retry))
            time.sleep(10)

    if r.status_code == 200:
        r_cache.hset('metadata_crawler:{}'.format(splash_url), 'status', 'Crawling')
        # save config in cash
        UUID = str(uuid.uuid4())
        r_cache.set('crawler_request:{}'.format(UUID), json.dumps(crawler_config))

        process = subprocess.Popen(["python", './torcrawler/tor_crawler.py', UUID],
                                   stdout=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(1)

        if process.returncode == 0:
            output = process.stdout.read().decode()
            print(output)
            # error: splash:Connection to proxy refused
            if 'Connection to proxy refused' in output:
                on_error_send_message_back_in_queue(type_service, domain, message)
                publisher.error('{} SPASH, PROXY DOWN OR BAD CONFIGURATION'.format(splash_url))
                print('------------------------------------------------------------------------')
                print('         \033[91m SPLASH: Connection to proxy refused')
                print('')
                print('            PROXY DOWN OR BAD CONFIGURATION\033[0m'.format(splash_url))
                print('------------------------------------------------------------------------')
                r_cache.hset('metadata_crawler:{}'.format(splash_url), 'status', 'Error')
                exit(-2)
            else:
                crawlers.update_splash_manager_connection_status(True)
        else:
            print(process.stdout.read())
            exit(-1)
    else:
        on_error_send_message_back_in_queue(type_service, domain, message)
        print('--------------------------------------')
        print('         \033[91m DOCKER SPLASH DOWN\033[0m')
        print('          {} DOWN'.format(splash_url))
        r_cache.hset('metadata_crawler:{}'.format(splash_url), 'status', 'Crawling')
        exit(1)

# check external links (full_crawl)
def search_potential_source_domain(type_service, domain):
    external_domains = set()
    for link in redis_crawler.smembers('domain_{}_external_links:{}'.format(type_service, domain)):
        # unpack url
        url_data = unpack_url(link)
        if url_data['domain'] != domain:
            if url_data['tld'] == 'onion' or url_data['tld'] == 'i2p':
                external_domains.add(url_data['domain'])
    # # TODO: add special tag ?
    if len(external_domains) >= 20:
        redis_crawler.sadd('{}_potential_source'.format(type_service), domain)
        print('New potential source found: domain')
    redis_crawler.delete('domain_{}_external_links:{}'.format(type_service, domain))


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('usage:', 'Crawler.py', 'splash_url')
        exit(1)
##################################################
    splash_url = sys.argv[1]

    splash_name = crawlers.get_splash_name_by_url(splash_url)
    proxy_name = crawlers.get_splash_proxy(splash_name)
    crawler_type = crawlers.get_splash_crawler_type(splash_name)

    print(f'SPLASH Name:   {splash_name}')
    print(f'Proxy Name:    {proxy_name}')
    print(f'Crawler Type:  {crawler_type}')

    #time.sleep(10)
    #sys.exit(0)

    #rotation_mode = deque(['onion', 'regular'])
    all_crawler_queues = crawlers.get_crawler_queue_types_by_splash_name(splash_name)
    rotation_mode = deque(all_crawler_queues)
    print(rotation_mode)

    default_proto_map = {'http': 80, 'https': 443}
######################################################## add ftp ???

    publisher.port = 6380
    publisher.channel = "Script"
    publisher.info("Script Crawler started")
    config_section = 'Crawler'

    # Setup the I/O queues
    p = Process(config_section)

    print('splash url: {}'.format(splash_url))

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

    redis_crawler = redis.StrictRedis(
        host=p.config.get("ARDB_Onion", "host"),
        port=p.config.getint("ARDB_Onion", "port"),
        db=p.config.getint("ARDB_Onion", "db"),
        decode_responses=True)

    faup = crawlers.get_faup()

    # get HAR files
    default_crawler_har = p.config.getboolean("Crawler", "default_crawler_har")
    if default_crawler_har:
        default_crawler_har = True
    else:
        default_crawler_har = False

    # get PNG files
    default_crawler_png = p.config.getboolean("Crawler", "default_crawler_png")
    if default_crawler_png:
        default_crawler_png = True
    else:
        default_crawler_png = False

    # Default crawler options
    default_crawler_config = {'html': True,
                              'har': default_crawler_har,
                              'png': default_crawler_png,
                              'depth_limit': p.config.getint("Crawler", "crawler_depth_limit"),
                              'closespider_pagecount': p.config.getint("Crawler", "default_crawler_closespider_pagecount"),
                              'cookiejar_uuid': None,
                              'user_agent': p.config.get("Crawler", "default_crawler_user_agent")}

    # Track launched crawler
    r_cache.sadd('all_splash_crawlers', splash_url)
    r_cache.hset('metadata_crawler:{}'.format(splash_url), 'status', 'Waiting')
    r_cache.hset('metadata_crawler:{}'.format(splash_url), 'started_time', datetime.datetime.now().strftime("%Y/%m/%d  -  %H:%M.%S"))

    # update hardcoded blacklist
    load_blacklist('onion')
    load_blacklist('regular')

    while True:

        update_auto_crawler()

        rotation_mode.rotate()
        to_crawl = crawlers.get_elem_to_crawl_by_queue_type(rotation_mode)
        if to_crawl:
            url_data = unpack_url(to_crawl['url'])
            # remove domain from queue
            redis_crawler.srem('{}_domain_crawler_queue'.format(to_crawl['type_service']), url_data['domain'])

            print()
            print()
            print('\033[92m------------------START CRAWLER------------------\033[0m')
            print('crawler type:     {}'.format(to_crawl['type_service']))
            print('\033[92m-------------------------------------------------\033[0m')
            print('url:         {}'.format(url_data['url']))
            print('domain:      {}'.format(url_data['domain']))
            print('domain_url:  {}'.format(url_data['domain_url']))
            print()

            # Check blacklist
            if not redis_crawler.sismember('blacklist_{}'.format(to_crawl['type_service']), url_data['domain']):
                date = {'date_day': datetime.datetime.now().strftime("%Y%m%d"),
                        'date_month': datetime.datetime.now().strftime("%Y%m"),
                        'epoch': int(time.time())}

                # Update crawler status type
                r_cache.hset('metadata_crawler:{}'.format(splash_url), 'type', to_crawl['type_service'])

                crawler_config = load_crawler_config(to_crawl['queue_type'], to_crawl['type_service'], url_data['domain'], to_crawl['paste'],  to_crawl['url'], date)
                # check if default crawler
                if not crawler_config['requested']:
                    # Auto crawl only if service not up this month
                    if redis_crawler.sismember('month_{}_up:{}'.format(to_crawl['type_service'], date['date_month']), url_data['domain']):
                        continue

                set_crawled_domain_metadata(to_crawl['type_service'], date, url_data['domain'], to_crawl['paste'])


                #### CRAWLER ####
                # Manual and Auto Crawler
                if crawler_config['requested']:

                ######################################################crawler strategy
                    # CRAWL domain
                    crawl_onion(url_data['url'], url_data['domain'], url_data['port'], to_crawl['type_service'], to_crawl['original_message'], crawler_config)

                # Default Crawler
                else:
                    # CRAWL domain
                    crawl_onion(url_data['domain_url'], url_data['domain'], url_data['port'], to_crawl['type_service'], to_crawl['original_message'], crawler_config)
                    #if url != domain_url and not is_domain_up_day(url_data['domain'], to_crawl['type_service'], date['date_day']):
                    #    crawl_onion(url_data['url'], url_data['domain'], to_crawl['original_message'])


                # Save last_status day (DOWN)
                if not is_domain_up_day(url_data['domain'], to_crawl['type_service'], date['date_day']):
                    redis_crawler.sadd('{}_down:{}'.format(to_crawl['type_service'], date['date_day']), url_data['domain'])

                # if domain was UP at least one time
                if redis_crawler.exists('crawler_history_{}:{}:{}'.format(to_crawl['type_service'], url_data['domain'], url_data['port'])):
                    # add crawler history (if domain is down)
                    if not redis_crawler.zrangebyscore('crawler_history_{}:{}:{}'.format(to_crawl['type_service'], url_data['domain'], url_data['port']), date['epoch'], date['epoch']):
                        # Domain is down
                        redis_crawler.zadd('crawler_history_{}:{}:{}'.format(to_crawl['type_service'], url_data['domain'], url_data['port']), int(date['epoch']), int(date['epoch']))

                        ############################
                        # extract page content
                        ############################

                # update list, last crawled domains
                redis_crawler.lpush('last_{}'.format(to_crawl['type_service']), '{}:{};{}'.format(url_data['domain'], url_data['port'], date['epoch']))
                redis_crawler.ltrim('last_{}'.format(to_crawl['type_service']), 0, 15)

                #update crawler status
                r_cache.hset('metadata_crawler:{}'.format(splash_url), 'status', 'Waiting')
                r_cache.hdel('metadata_crawler:{}'.format(splash_url), 'crawling_domain')

                # Update crawler status type
                r_cache.hdel('metadata_crawler:{}'.format(splash_url), 'type', to_crawl['type_service'])

                # add next auto Crawling in queue:
                if to_crawl['paste'] == 'auto':
                    redis_crawler.zadd('crawler_auto_queue', int(time.time()+crawler_config['crawler_options']['time']) , '{};{}'.format(to_crawl['original_message'], to_crawl['type_service']))
                    # update list, last auto crawled domains
                    redis_crawler.lpush('last_auto_crawled', '{}:{};{}'.format(url_data['domain'], url_data['port'], date['epoch']))
                    redis_crawler.ltrim('last_auto_crawled', 0, 9)
            else:
                print('                 Blacklisted Domain')
                print()
                print()

        else:
            time.sleep(1)

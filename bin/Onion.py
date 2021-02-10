#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The ZMQ_Sub_Onion Module
============================

This module is consuming the Redis-list created by the ZMQ_Sub_Onion_Q Module.

It trying to extract url from paste and returning only ones which are tor
related (.onion)

    ..seealso:: Paste method (get_regex)

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances. (Redis)
*Need the ZMQ_Sub_Onion_Q Module running to be able to work properly.

"""
import time
from packages import Paste
from pubsublogger import publisher
import datetime
import os
import base64
import subprocess
import redis
import signal
import re

from pyfaup.faup import Faup

from Helper import Process

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

def fetch(p, r_cache, urls, domains, path):
    failed = []
    downloaded = []
    print('{} Urls to fetch'.format(len(urls)))
    for url, domain in zip(urls, domains):
        if r_cache.exists(url) or url in failed:
            continue
        to_fetch = base64.standard_b64encode(url.encode('utf8'))
        print('fetching url: {}'.format(to_fetch))
        process = subprocess.Popen(["python", './tor_fetcher.py', to_fetch],
                                   stdout=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(1)

        if process.returncode == 0:
            r_cache.setbit(url, 0, 1)
            r_cache.expire(url, 360000)
            downloaded.append(url)
            print('downloaded : {}'.format(downloaded))
            '''tempfile = process.stdout.read().strip()
            tempfile = tempfile.decode('utf8')
            #with open(tempfile, 'r') as f:
                filename = path + domain + '.gz'
                fetched = f.read()
                content = base64.standard_b64decode(fetched)
                save_path = os.path.join(os.environ['AIL_HOME'],
                                         p.config.get("Directories", "pastes"),
                                         filename)
                dirname = os.path.dirname(save_path)
                if not os.path.exists(dirname):
                    os.makedirs(dirname)
                with open(save_path, 'w') as ff:
                    ff.write(content)
                p.populate_set_out(save_path, 'Global')
                p.populate_set_out(url, 'ValidOnion')
                p.populate_set_out(fetched, 'FetchedOnion')'''
            yield url
            #os.unlink(tempfile)
        else:
            r_cache.setbit(url, 0, 0)
            r_cache.expire(url, 3600)
            failed.append(url)
            print('Failed at downloading', url)
            print(process.stdout.read())
    print('Failed:', len(failed), 'Downloaded:', len(downloaded))


if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    torclient_host = '127.0.0.1'
    torclient_port = 9050

    config_section = 'Onion'

    p = Process(config_section)
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

    # FUNCTIONS #
    publisher.info("Script subscribed to channel onion_categ")

    # FIXME For retro compatibility
    channel = 'onion_categ'

    # Getting the first message from redis.
    message = p.get_from_set()
    prec_filename = None

    max_execution_time = p.config.getint("Onion", "max_execution_time")

    # send to crawler:
    activate_crawler = p.config.get("Crawler", "activate_crawler")
    if activate_crawler == 'True':
        activate_crawler = True
        print('Crawler enabled')
    else:
        activate_crawler = False
        print('Crawler disabled')

    faup = Faup()

    # Thanks to Faup project for this regex
    # https://github.com/stricaud/faup
    url_regex = "((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.onion)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
    i2p_regex = "((http|https|ftp)?(?:\://)?([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.i2p)(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*)"
    re.compile(url_regex)


    while True:
        message = p.get_from_set()
        if message is not None:
            print(message)
            filename, score = message.split()

            # "For each new paste"
            if prec_filename is None or filename != prec_filename:
                domains_list = []
                urls = []
                PST = Paste.Paste(filename)

                # max execution time on regex
                signal.alarm(max_execution_time)
                try:
                    for x in PST.get_regex(url_regex):
                        print(x)
                        # Extracting url with regex
                        url, s, credential, subdomain, domain, host, port, \
                            resource_path, query_string, f1, f2, f3, f4 = x

                        if '.onion' in url:
                            print(url)
                            domains_list.append(domain)
                            urls.append(url)
                except TimeoutException:
                    encoded_list = []
                    p.incr_module_timeout_statistic()
                    print ("{0} processing timeout".format(PST.p_rel_path))
                    continue

                signal.alarm(0)

                '''
                for x in PST.get_regex(i2p_regex):
                    # Extracting url with regex
                    url, s, credential, subdomain, domain, host, port, \
                        resource_path, query_string, f1, f2, f3, f4 = x

                    if '.i2p' in url:
                        print('add i2p')
                        print(domain)
                        if not r_onion.sismember('i2p_domain', domain) and not r_onion.sismember('i2p_domain_crawler_queue', domain):
                            r_onion.sadd('i2p_domain', domain)
                            r_onion.sadd('i2p_link', url)
                            r_onion.sadd('i2p_domain_crawler_queue', domain)
                            msg = '{};{}'.format(url,PST.p_rel_path)
                            r_onion.sadd('i2p_crawler_queue', msg)
                '''

                to_print = 'Onion;{};{};{};'.format(PST.p_source, PST.p_date,
                                                    PST.p_name)

                print(len(domains_list))
                if len(domains_list) > 0:

                    if not activate_crawler:
                        publisher.warning('{}Detected {} .onion(s);{}'.format(
                            to_print, len(domains_list),PST.p_rel_path))
                    else:
                        publisher.info('{}Detected {} .onion(s);{}'.format(
                            to_print, len(domains_list),PST.p_rel_path))
                    now = datetime.datetime.now()
                    path = os.path.join('onions', str(now.year).zfill(4),
                                        str(now.month).zfill(2),
                                        str(now.day).zfill(2),
                                        str(int(time.mktime(now.utctimetuple()))))
                    to_print = 'Onion;{};{};{};'.format(PST.p_source,
                                                        PST.p_date,
                                                        PST.p_name)

                    if activate_crawler:
                        date_month = datetime.datetime.now().strftime("%Y%m")
                        date = datetime.datetime.now().strftime("%Y%m%d")
                        for url in urls:

                            faup.decode(url)
                            url_unpack = faup.get()
                            ## TODO: # FIXME: remove me
                            try:
                                domain = url_unpack['domain'].decode().lower()
                            except Exception as e:
                                 domain = url_unpack['domain'].lower()

                            ## TODO: blackilst by port ?
                            # check blacklist
                            if r_onion.sismember('blacklist_onion', domain):
                                continue

                            subdomain = re.findall(url_regex, url)
                            if len(subdomain) > 0:
                                subdomain = subdomain[0][4].lower()
                            else:
                                continue

                            # too many subdomain
                            if len(subdomain.split('.')) > 3:
                                subdomain = '{}.{}.onion'.format(subdomain[-3], subdomain[-2])

                            if not r_onion.sismember('month_onion_up:{}'.format(date_month), subdomain) and not r_onion.sismember('onion_down:'+date , subdomain):
                                if not r_onion.sismember('onion_domain_crawler_queue', subdomain):
                                    print('send to onion crawler')
                                    r_onion.sadd('onion_domain_crawler_queue', subdomain)
                                    msg = '{};{}'.format(url,PST.p_rel_path)
                                    if not r_onion.hexists('onion_metadata:{}'.format(subdomain), 'first_seen'):
                                        r_onion.sadd('onion_crawler_discovery_queue', msg)
                                        print('send to priority queue')
                                    else:
                                        r_onion.sadd('onion_crawler_queue', msg)
                            # tag if domain was up
                            if r_onion.sismember('full_onion_up', subdomain):
                                # TAG Item
                                msg = 'infoleak:automatic-detection="onion";{}'.format(PST.p_rel_path)
                                p.populate_set_out(msg, 'Tags')

                    else:
                        for url in fetch(p, r_cache, urls, domains_list, path):
                            publisher.info('{}Checked {};{}'.format(to_print, url, PST.p_rel_path))

                    # TAG Item
                    msg = 'infoleak:automatic-detection="onion";{}'.format(PST.p_rel_path)
                    p.populate_set_out(msg, 'Tags')
                else:
                    publisher.info('{}Onion related;{}'.format(to_print, PST.p_rel_path))

            prec_filename = filename
        else:
            publisher.debug("Script url is Idling 10s")
            #print('Sleeping')
            time.sleep(10)

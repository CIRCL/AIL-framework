#!/usr/bin/env python3
# -*-coding:UTF-8 -*

from packages import Paste
from Helper import Process

import os
import re
import time
import redis
import configparser

from collections import defaultdict

def get_dict_cve(list_paste_cve, only_one_same_cve_by_paste=False):
    dict_keyword = {}

    for paste_cve in list_paste_cve:
        paste_content = Paste.Paste(paste_cve).get_p_content()

        cve_list = reg_cve.findall(paste_content)
        if only_one_same_cve_by_paste:
            cve_list = set(cve_list)

        for cve in reg_cve.findall(paste_content):
            try:
                dict_keyword[cve] += 1
            except KeyError:
                dict_keyword[cve] = 1

    print('------------------------------------------------')
    if dict_keyword:
        res = [(k, dict_keyword[k]) for k in sorted(dict_keyword, key=dict_keyword.get, reverse=True)]
        for item in res:
            pass
            print(item)



if __name__ == '__main__':

    # CONFIG #
    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    serv_metadata = redis.StrictRedis(
        host=cfg.get("ARDB_Metadata", "host"),
        port=cfg.getint("ARDB_Metadata", "port"),
        db=cfg.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    serv_tags = redis.StrictRedis(
                host=cfg.get("ARDB_Tags", "host"),
                port=cfg.get("ARDB_Tags", "port"),
                db=cfg.get("ARDB_Tags", "db"),
                decode_responses=True)

    reg_cve = re.compile(r'CVE-[1-2]\d{1,4}-\d{1,7}')

    #all_past_cve = serv_tags.smembers('infoleak:automatic-detection="cve"')
    #all_past_cve_regular = serv_tags.sdiff('infoleak:automatic-detection="cve"', 'infoleak:submission="crawler"')
    #all_past_cve_crawler = serv_tags.sinter('infoleak:automatic-detection="cve"', 'infoleak:submission="crawler"')

    #print('{} + {} = {}'.format(len(all_past_cve_regular), len(all_past_cve_crawler), len(all_past_cve)))

    print('ALL_CVE')
    get_dict_cve(serv_tags.smembers('infoleak:automatic-detection="cve"'), True)
    print()
    print()
    print()
    print('REGULAR_CVE')
    get_dict_cve(serv_tags.sdiff('infoleak:automatic-detection="cve"', 'infoleak:submission="crawler"'), True)
    print()
    print()
    print()
    print('CRAWLER_CVE')
    get_dict_cve(serv_tags.sinter('infoleak:automatic-detection="cve"', 'infoleak:submission="crawler"'), True)

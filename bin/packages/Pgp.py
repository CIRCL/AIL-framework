#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

from hashlib import sha256

sys.path.append(os.path.join(os.environ['AIL_FLASK'], 'modules'))
import Flask_config

from Correlation import Correlation
import Item

serv_metadata = Flask_config.r_serv_metadata

pgpdump = Correlation('pgpdump')


def get_pgp(request_dict, pgp_type):
    # basic verification
    res = pgpdump.verify_correlation_field_request(request_dict, pgp_type)
    if res:
        return res
    # cerify address
    field_name = request_dict.get(pgp_type)

    return pgpdump.get_correlation(request_dict, pgp_type, field_name)

def save_pgp_data(type_pgp, date, item_path, data):
    # create basic medata
    if not serv_metadata.exists('pgpdump_metadata_{}:{}'.format(type_pgp, data)):
        serv_metadata.hset('pgpdump_metadata_{}:{}'.format(type_pgp, data), 'first_seen', date)
        serv_metadata.hset('pgpdump_metadata_{}:{}'.format(type_pgp, data), 'last_seen', date)
    else:
        last_seen = serv_metadata.hget('pgpdump_metadata_{}:{}'.format(type_pgp, data), 'last_seen')
        if not last_seen:
            serv_metadata.hset('pgpdump_metadata_{}:{}'.format(type_pgp, data), 'last_seen', date)
        else:
            if int(last_seen) < int(date):
                serv_metadata.hset('pgpdump_metadata_{}:{}'.format(type_pgp, data), 'last_seen', date)

    # global set
    serv_metadata.sadd('set_pgpdump_{}:{}'.format(type_pgp, data), item_path)

    # daily
    serv_metadata.hincrby('pgpdump:{}:{}'.format(type_pgp, date), data, 1)

    # all type
    serv_metadata.zincrby('pgpdump_all:{}'.format(type_pgp), data, 1)

    ## object_metadata
    # paste
    serv_metadata.sadd('item_pgpdump_{}:{}'.format(type_pgp, item_path), data)


    # domain object
    if Item.is_crawled(item_path):
        domain = Item.get_item_domain(item_path)
        serv_metadata.sadd('domain_pgpdump_{}:{}'.format(type_pgp, domain), data)
        serv_metadata.sadd('set_domain_pgpdump_{}:{}'.format(type_pgp, data), domain)

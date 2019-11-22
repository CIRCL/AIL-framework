#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Cryptocurrency

blockchain_all='https://blockchain.info/rawaddr'

# pre-alpha script

# default nb_transactions = 50
def get_bitcoin_info(bitcoin_address, nb_transaction=50):
    dict_btc = {}
    set_btc_in = set()
    set_btc_out = set()
    req = None
    try:
        req = requests.get('{}/{}?limit={}'.format(blockchain_all, bitcoin_address, nb_transaction))
        jreq = req.json()
    except Exception as e:
        print(e)
        return dict_btc

    #print(json.dumps(jreq))
    dict_btc['n_tx'] = jreq['n_tx']
    dict_btc['total_received'] = float(jreq['total_received'] / 100000000)
    dict_btc['total_sent'] = float(jreq['total_sent'] / 100000000)
    dict_btc['final_balance'] = float(jreq['final_balance'] / 100000000)

    for transaction in jreq['txs']:
        for input in transaction['inputs']:
            if input['prev_out']['addr'] != bitcoin_address:
                set_btc_in.add(input['prev_out']['addr'])
        for output in transaction['out']:
            if output['addr'] != bitcoin_address:
                set_btc_out.add(output['addr'])

    dict_btc['btc_in'] = filter_btc_seen(set_btc_in)
    dict_btc['btc_out'] = filter_btc_seen(set_btc_out)
    return dict_btc

# filter btc seen in ail
def filter_btc_seen(btc_addr_set):
    list_seen_btc = []
    for btc_addr in btc_addr_set:
        if Cryptocurrency.cryptocurrency._exist_corelation_field('bitcoin', btc_addr):
            list_seen_btc.append(btc_addr)
    return list_seen_btc

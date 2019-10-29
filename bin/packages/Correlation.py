#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

sys.path.append(os.path.join(os.environ['AIL_FLASK'], 'modules/'))
import Flask_config

r_serv_metadata = Flask_config.r_serv_metadata


class Correlation(object):

    def __init__(self, correlation_name):
        self.correlation_name = correlation_name

    def _exist_corelation_field(self, correlation_type, field_name, item_type='paste'):
        if type=='paste':
            return r_serv_metadata.exists('set_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))
        else:
            return r_serv_metadata.exists('set_domain_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))

    def _get_items(self, correlation_type, field_name):
        res =  r_serv_metadata.smembers('set_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))
        if res:
            return list(res)
        else:
            return []

    def _get_domains(self, correlation_type, field_name):
        res =  r_serv_metadata.smembers('set_domain_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))
        if res:
            return list(res)
        else:
            return []

    def _get_metadata(self, correlation_type, field_name):
        meta_dict = {}
        meta_dict['first_seen'] = r_serv_metadata.hget('{}_metadata_{}:{}'.format(self.correlation_name, correlation_type, field_name), 'first_seen')
        meta_dict['last_seen'] = r_serv_metadata.hget('{}_metadata_{}:{}'.format(self.correlation_name, correlation_type, field_name), 'last_seen')
        return meta_dict

    def _get_correlation_by_date(self, correlation_type, date):
        return r_serv_metadata.hkeys('{}:{}:{}'.format(self.correlation_name, correlation_type, date))

    def verify_correlation_field_request(self, request_dict, correlation_type, item_type='paste'):
        if not request_dict:
            return ({'status': 'error', 'reason': 'Malformed JSON'}, 400)

        print(correlation_type)
        field_name = request_dict.get(correlation_type, None)
        if not field_name:
            return ( {'status': 'error', 'reason': 'Mandatory parameter(s) not provided'}, 400 )
        if not self._exist_corelation_field(correlation_type, field_name, item_type=item_type):
            return ( {'status': 'error', 'reason': 'Item not found'}, 404 )

    def get_correlation(self, request_dict, correlation_type, field_name):
        dict_resp = {}

        if request_dict.get('items'):
            dict_resp['items'] = self._get_items(correlation_type, field_name)

        if request_dict.get('metadata'):
            dict_resp['metadata'] = self._get_metadata(correlation_type, field_name)

        dict_resp[correlation_type] = field_name

        return (dict_resp, 200)

    def get_correlation_domain(self, request_dict, correlation_type, field_name):
        dict_resp = {}

        dict_resp['domain'] = self._get_domains(correlation_type, field_name)

        #if request_dict.get('metadata'):
        #    dict_resp['metadata'] = self._get_metadata(correlation_type, field_name)

        dict_resp[correlation_type] = field_name

        return (dict_resp, 200)

######## INTERNAL ########

def _get_domain_correlation_obj(correlation_name, correlation_type, domain):
    print('domain_{}_{}:{}'.format(correlation_name, correlation_type, domain))
    res = r_serv_metadata.smembers('domain_{}_{}:{}'.format(correlation_name, correlation_type, domain))
    if res:
        return list(res)
    else:
        return []

########  ########

######## API EXPOSED ########

def get_domain_correlation_obj(request_dict, correlation_name, correlation_type, domain):
    dict_resp = {}
    dict_resp[correlation_type] = _get_domain_correlation_obj(correlation_name, correlation_type, domain)
    dict_resp['domain'] = domain

    return (dict_resp, 200)

########  ########

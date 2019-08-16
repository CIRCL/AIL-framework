#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import redis

import Flask_config

r_serv_metadata = Flask_config.r_serv_metadata


class Correlation(object):

    def __init__(self, correlation_name):
        self.correlation_name = correlation_name

    def _exist_corelation_field(self, correlation_type, field_name):
        return r_serv_metadata.exists('set_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))


    def _get_items(self, correlation_type, field_name):
        res =  r_serv_metadata.smembers('set_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))
        if res:
            return list(res)
        else:
            return {}


    def _get_metadata(self, correlation_type, field_name):
        meta_dict = {}
        meta_dict['first_seen'] = r_serv_metadata.hget('{}_metadata_{}:{}'.format(self.correlation_name, correlation_type, field_name), 'first_seen')
        meta_dict['last_seen'] = r_serv_metadata.hget('{}_metadata_{}:{}'.format(self.correlation_name, correlation_type, field_name), 'last_seen')
        return meta_dict

    def _get_correlation_by_date(self, correlation_type, date):
        return r_serv_metadata.hkeys('{}:{}:{}'.format(self.correlation_name, correlation_type, date))

    def verify_correlation_field_request(self, request_dict, correlation_type):
        if not request_dict:
            return Response({'status': 'error', 'reason': 'Malformed JSON'}, 400)

        field_name = request_dict.get(correlation_type, None)
        if not field_name:
            return ( {'status': 'error', 'reason': 'Mandatory parameter(s) not provided'}, 400 )
        if not self._exist_corelation_field(correlation_type, field_name):
            return ( {'status': 'error', 'reason': 'Item not found'}, 404 )

    def get_correlation(self, request_dict, correlation_type, field_name):
        dict_resp = {}

        if request_dict.get('items'):
            dict_resp['items'] = self._get_items(correlation_type, field_name)

        if request_dict.get('metadata'):
            dict_resp['metadata'] = self._get_metadata(correlation_type, field_name)

        dict_resp[correlation_type] = field_name

        return (dict_resp, 200)




#cryptocurrency_all:cryptocurrency name	cryptocurrency address	nb seen

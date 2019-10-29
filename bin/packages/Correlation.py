#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

sys.path.append(os.path.join(os.environ['AIL_FLASK'], 'lib/'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

class Correlation(object):

    def __init__(self, correlation_name, all_correlation_types):
        self.correlation_name = correlation_name
        self.all_correlation_types = all_correlation_types

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

    def get_all_correlation_types(self):
        '''
        Gel all correlation types

        :return: A list of all the correlation types
        :rtype: list
        '''
        return self.all_correlation_types

    def sanythise_correlation_types(self, correlation_types):
        '''
        Check if all correlation types in the list are valid.

        :param correlation_types: list of correlation type
        :type currency_type: list

        :return: If a type is invalid, return the full list of correlation types else return the provided list
        :rtype: list
        '''
        if correlation_types is None:
            return self.get_all_correlation_types()
        for correl in correlation_types: # # TODO: # OPTIMIZE:
            if correl not in self.get_all_correlation_types():
                return self.get_all_correlation_types()
        return correlation_types


    def _get_domain_correlation_obj(self, domain, correlation_type):
        '''
        Return correlation of a given domain.

        :param domain: crawled domain
        :type domain: str
        :param correlation_type: correlation type
        :type correlation_type: str

        :return: a list of correlation
        :rtype: list
        '''
        res = r_serv_metadata.smembers('domain_{}_{}:{}'.format(self.correlation_name, correlation_type, domain))
        if res:
            return list(res)
        else:
            return []

    def get_domain_correlation_dict(self, domain, correlation_type=None):
        '''
        Return all correlation of a given domain.

        :param domain: crawled domain
        :param correlation_type: list of correlation types
        :type correlation_type: list, optional

        :return: a dictionnary of all the requested correlations
        :rtype: dict
        '''
        correlation_type = self.sanythise_correlation_types(correlation_type)
        dict_correlation = {}
        for correl in correlation_type:
            res = self._get_domain_correlation_obj(domain, correl)
            if res:
                dict_correlation[correl] = res
        return dict_correlation


######## API EXPOSED ########


########  ########

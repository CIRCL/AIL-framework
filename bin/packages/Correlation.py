#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Date

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

class Correlation(object):

    def __init__(self, correlation_name, all_correlation_types):
        self.correlation_name = correlation_name
        self.all_correlation_types = all_correlation_types

    def _exist_corelation_field(self, correlation_type, field_name, item_type='paste'):
        if item_type=='paste':
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
        meta_dict['nb_seen'] = r_serv_metadata.scard('set_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))
        return meta_dict

    def get_metadata(self, correlation_type, field_name, date_format='str_date'):
        meta_dict = self._get_metadata(correlation_type, field_name)
        if date_format == "str_date":
            if meta_dict['first_seen']:
                meta_dict['first_seen'] = '{}/{}/{}'.format(meta_dict['first_seen'][0:4], meta_dict['first_seen'][4:6], meta_dict['first_seen'][6:8])
            if meta_dict['last_seen']:
                meta_dict['last_seen'] = '{}/{}/{}'.format(meta_dict['last_seen'][0:4], meta_dict['last_seen'][4:6], meta_dict['last_seen'][6:8])
        return meta_dict

    def get_nb_object_seen_by_date(self, correlation_type, field_name, date_day):
        nb = r_serv_metadata.hget('{}:{}:{}'.format(self.correlation_name, correlation_type, date_day), field_name)
        if nb is None:
            return 0
        else:
            return int(nb)

    def get_list_nb_previous_correlation_object(self, correlation_type, field_name, numDay):
        nb_previous_correlation = []
        for date_day in Date.get_previous_date_list(numDay):
            nb_previous_correlation.append(self.get_nb_object_seen_by_date(correlation_type, field_name, date_day))
        return nb_previous_correlation

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

    def get_domain_correlation_dict(self, domain, correlation_type=None, get_nb=False):
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
                if get_nb:
                    dict_correlation['nb'] = dict_correlation.get('nb', 0) + len(dict_correlation[correl])
        return dict_correlation

    def _get_correlation_obj_domain(self, field_name, correlation_type):
        '''
        Return all domains that contain this correlation.

        :param domain: field name
        :type domain: str
        :param correlation_type: correlation type
        :type correlation_type: str

        :return: a list of correlation
        :rtype: list
        '''
        res = r_serv_metadata.smembers('set_domain_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))
        if res:
            return list(res)
        else:
            return []

    def get_correlation_obj_domain(self, field_name, correlation_type=None):
        '''
        Return all domain correlation of a given correlation_value.

        :param field_name: field_name
        :param correlation_type: list of correlation types
        :type correlation_type: list, optional

        :return: a dictionnary of all the requested correlations
        :rtype: list
        '''
        correlation_type = self.sanythise_correlation_types(correlation_type)
        for correl in correlation_type:
            res = self._get_correlation_obj_domain(field_name, correl)
            if res:
                return res
        return []



    def _get_item_correlation_obj(self, item_id, correlation_type):
        '''
        Return correlation of a given item id.

        :param item_id: item id
        :type item_id: str
        :param correlation_type: correlation type
        :type correlation_type: str

        :return: a list of correlation
        :rtype: list
        '''
        res = r_serv_metadata.smembers('item_{}_{}:{}'.format(self.correlation_name, correlation_type, item_id))
        if res:
            return list(res)
        else:
            return []

    def get_item_correlation_dict(self, item_id, correlation_type=None, get_nb=False):
        '''
        Return all correlation of a given item id.

        :param item_id: item id
        :param correlation_type: list of correlation types
        :type correlation_type: list, optional

        :return: a dictionnary of all the requested correlations
        :rtype: dict
        '''
        correlation_type = self.sanythise_correlation_types(correlation_type)
        dict_correlation = {}
        for correl in correlation_type:
            res = self._get_item_correlation_obj(item_id, correl)
            if res:
                dict_correlation[correl] = res
                if get_nb:
                    dict_correlation['nb'] = dict_correlation.get('nb', 0) + len(dict_correlation[correl])
        return dict_correlation


    def get_correlation_all_object(self, correlation_type, correlation_value, correlation_objects=[]):
        if correlation_objects is None:
            correlation_objects = get_all_correlation_objects()
        correlation_obj = {}
        for correlation_object in correlation_objects:
            if correlation_object == 'paste':
                res = self._get_items(correlation_type, correlation_value)
            elif correlation_object == 'domain':
                res = self.get_correlation_obj_domain(correlation_value, correlation_type=correlation_type)
            else:
                res = None
            if res:
                correlation_obj[correlation_object] = res
        return correlation_obj

    def save_domain_correlation(self, domain, correlation_type, correlation_value):
        r_serv_metadata.sadd('domain_{}_{}:{}'.format(self.correlation_name, correlation_type, domain), correlation_value)
        r_serv_metadata.sadd('set_domain_{}_{}:{}'.format(self.correlation_name, correlation_type, correlation_value), domain)



######## API EXPOSED ########


########  ########

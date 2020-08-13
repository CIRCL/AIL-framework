#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Date
import Item
#import Tag

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

def get_all_correlation_objects():
    '''
    Return a list of all correllated objects
    '''
    return ['domain', 'paste']

class SimpleCorrelation(object): #social_name

    def __init__(self, correlation_name):
        self.correlation_name = correlation_name

    def exist_correlation(self, obj_id):
        res = r_serv_metadata.zscore('s_correl:{}:all'.format(self.correlation_name), obj_id)
        if res is not None:
            return True
        else:
            return False

    def _get_items(self, obj_id):
        res =  r_serv_metadata.smembers('s_correl:set_item_{}:{}'.format(self.correlation_name, obj_id))
        if res:
            return list(res)
        else:
            return []

    def get_correlation_first_seen(self, obj_id, r_int=False):
        res = r_serv_metadata.hget('s_correl:{}:metadata:{}'.format(self.correlation_name, obj_id), 'first_seen')
        if r_int:
            if res:
                return int(res)
            else:
                return 99999999
        else:
            return res

    def get_correlation_last_seen(self, obj_id, r_int=False):
        res = r_serv_metadata.hget('s_correl:{}:metadata:{}'.format(self.correlation_name, obj_id), 'last_seen')
        if r_int:
            if res:
                return int(res)
            else:
                return 0
        else:
            return res

    def _get_metadata(self, obj_id):
        meta_dict = {}
        meta_dict['first_seen'] = self.get_correlation_first_seen(obj_id)
        meta_dict['last_seen'] = self.get_correlation_last_seen(obj_id)
        meta_dict['nb_seen'] = r_serv_metadata.scard('s_correl:set_item_{}:{}'.format(self.correlation_name, obj_id))
        return meta_dict

    def get_metadata(self, correlation_type, field_name, date_format='str_date'):
        meta_dict = self._get_metadata(obj_id)
        if date_format == "str_date":
            if meta_dict['first_seen']:
                meta_dict['first_seen'] = '{}/{}/{}'.format(meta_dict['first_seen'][0:4], meta_dict['first_seen'][4:6], meta_dict['first_seen'][6:8])
            if meta_dict['last_seen']:
                meta_dict['last_seen'] = '{}/{}/{}'.format(meta_dict['last_seen'][0:4], meta_dict['last_seen'][4:6], meta_dict['last_seen'][6:8])
        return meta_dict

    def get_nb_object_seen_by_date(self, obj_id, date_day):
        nb = r_serv_metadata.zscore('s_correl:date:{}:{}'.format(self.correlation_name, date_day), obj_id)
        if nb is None:
            return 0
        else:
            return int(nb)

    def get_list_nb_previous_correlation_object(self, obj_id, numDay):
        nb_previous_correlation = []
        for date_day in Date.get_previous_date_list(numDay):
            nb_previous_correlation.append(self.get_nb_object_seen_by_date(obj_id, date_day))
        return nb_previous_correlation

    def _get_correlation_by_date(self, date_day):
        return r_serv_metadata.zrange('s_correl:date:{}:{}'.format(self.correlation_name, date_day), 0, -1)

    # def verify_correlation_field_request(self, request_dict, correlation_type, item_type='paste'):
    #     if not request_dict:
    #         return ({'status': 'error', 'reason': 'Malformed JSON'}, 400)
    #
    #     field_name = request_dict.get(correlation_type, None)
    #     if not field_name:
    #         return ( {'status': 'error', 'reason': 'Mandatory parameter(s) not provided'}, 400 )
    #     if not self._exist_corelation_field(correlation_type, field_name, item_type=item_type):
    #         return ( {'status': 'error', 'reason': 'Item not found'}, 404 )

    def get_correlation(self, request_dict, obj_id):
        dict_resp = {}

        if request_dict.get('items'):
            dict_resp['items'] = self._get_items(obj_id)

        if request_dict.get('metadata'):
            dict_resp['metadata'] = self._get_metadata(obj_id)
        return (dict_resp, 200)

    def _get_domain_correlation_obj(self, domain):
        '''
        Return correlation of a given domain.

        :param domain: crawled domain
        :type domain: str
        :param correlation_type: correlation type
        :type correlation_type: str

        :return: a list of correlation
        :rtype: list
        '''
        res = r_serv_metadata.smembers('domain:s_correl:{}:{}'.format(self.correlation_name, domain))
        if res:
            return list(res)
        else:
            return []

    def _get_correlation_obj_domain(self, correlation_id):
        '''
        Return all domains that contain this correlation.

        :param domain: field name
        :type domain: str
        :param correlation_type: correlation type
        :type correlation_type: str

        :return: a list of correlation
        :rtype: list
        '''
        res = r_serv_metadata.smembers('s_correl:set_domain_{}:{}'.format(self.correlation_name, correlation_id))
        if res:
            return list(res)
        else:
            return []

    def _get_item_correlation_obj(self, item_id):
        '''
        Return correlation of a given item id.

        :param item_id: item id
        :type item_id: str

        :return: a list of correlation
        :rtype: list
        '''
        res = r_serv_metadata.smembers('item:s_correl:{}:{}'.format(self.correlation_name, item_id))
        if res:
            return list(res)
        else:
            return []

    def get_correlation_all_object(self, correlation_value, correlation_objects=[]):
        if not correlation_objects:
            correlation_objects = get_all_correlation_objects()
        correlation_obj = {}
        for correlation_object in correlation_objects:
            if correlation_object == 'paste':
                res = self._get_items(correlation_value)
            elif correlation_object == 'domain':
                res = self.get_correlation_obj_domain(correlation_value)
            else:
                res = None
            if res:
                correlation_obj[correlation_object] = res
        return correlation_obj

    def update_correlation_daterange(self, obj_id, date):
        date = int(date)
        # obj_id don't exit
        if not r_serv_metadata.exists('s_correl:{}:metadata:{}'.format(self.correlation_name, obj_id)):
            r_serv_metadata.hset('s_correl:{}:metadata:{}'.format(self.correlation_name, obj_id), 'first_seen', date)
            r_serv_metadata.hset('s_correl:{}:metadata:{}'.format(self.correlation_name, obj_id), 'last_seen', date)
        else:
            first_seen = self.get_correlation_last_seen(obj_id, r_int=True)
            last_seen = self.get_correlation_first_seen(obj_id, r_int=True)
            if date < first_seen:
                r_serv_metadata.hset('s_correl:{}:metadata:{}'.format(self.correlation_name, obj_id), 'first_seen', date)
            if date > last_seen:
                r_serv_metadata.hset('s_correl:{}:metadata:{}'.format(self.correlation_name, obj_id), 'last_seen', date)

    def save_item_correlation(self, obj_id, item_id, item_date):
        self.update_correlation_daterange(obj_id, item_date)
        # global set
        r_serv_metadata.sadd('s_correl:set_item_{}:{}'.format(self.correlation_name, obj_id), item_id)

        # daily
        r_serv_metadata.zincrby('s_correl:date:{}:{}'.format(self.correlation_name, item_date), obj_id, 1)

        # all correlation
        r_serv_metadata.zincrby('s_correl:{}:all'.format(self.correlation_name), obj_id, 1)

        # item
        r_serv_metadata.sadd('item:s_correl:{}:{}'.format(self.correlation_name, item_id), obj_id)

        # domain
        if Item.is_crawled(item_id):
            domain = Item.get_item_domain(item_id)
            self.save_domain_correlation(domain, subtype, obj_id)

    def delete_item_correlation(self, subtype, obj_id, item_id, item_date):
        #self.update_correlation_daterange ! # # TODO:
        r_serv_metadata.srem('s_correl:set_item_{}:{}'.format(self.correlation_name, obj_id), item_id)
        r_serv_metadata.srem('item:s_correl:{}:{}'.format(self.correlation_name, item_id), obj_id)

        res = r_serv_metadata.zincrby('s_correl:date:{}:{}'.format(self.correlation_name, item_date), obj_id, -1)
        if int(res) < 0: # remove last
            r_serv_metadata.zrem('s_correl:date:{}:{}'.format(self.correlation_name, item_date), obj_id)

        res = r_serv_metadata.zscore('s_correl:{}:all'.format(self.correlation_name), obj_id)
        if int(res) > 0:
            r_serv_metadata.zincrby('s_correl:{}:all'.format(self.correlation_name), obj_id, -1)

    def save_domain_correlation(self, domain, obj_id):
        r_serv_metadata.sadd('domain:s_correl:{}:{}'.format(self.correlation_name, domain), obj_id)
        r_serv_metadata.sadd('s_correl:set_domain_{}:{}'.format(self.correlation_name, obj_id), domain)

    def delete_domain_correlation(self, domain, obj_id):
        r_serv_metadata.srem('domain:s_correl:{}:{}'.format(self.correlation_name, domain), obj_id)
        r_serv_metadata.srem('s_correl:set_domain_{}:{}'.format(self.correlation_name, obj_id), domain)

    ######

    def save_correlation(self, obj_id, date_range):
        r_serv_metadata.zincrby('s_correl:{}:all'.format(self.correlation_name), obj_id, 0)
        self.update_correlation_daterange(obj_id, date_range['date_from'])
        if date_range['date_from'] != date_range['date_to']:
            self.update_correlation_daterange(obj_id, date_range['date_to'])
        return True

    def save_obj_relationship(self, obj_id, obj2_type, obj2_id):
        if obj2_type == 'domain':
            self.save_domain_correlation(obj2_id, obj_id)
        elif obj2_type == 'item':
            self.save_item_correlation(obj_id, obj2_id, Item.get_item_date(obj2_id))

    def delete_obj_relationship(self, obj_id, obj2_type, obj2_id):
        if obj2_type == 'domain':
            self.delete_domain_correlation(obj2_id, obj_id)
        elif obj2_type == 'item':
            self.delete_item_correlation(obj_id, obj2_id, Item.get_item_date(obj2_id))

    # def create_correlation(self, subtype, obj_id, obj_meta):
    #     res = self.sanythise_correlation_types([subtype], r_boolean=True)
    #     if not res:
    #         print('invalid subtype')
    #         return False
    #     first_seen = obj_meta.get('first_seen', None)
    #     last_seen = obj_meta.get('last_seen', None)
    #     date_range = Date.sanitise_date_range(first_seen, last_seen, separator='', date_type='datetime')
    #     res = self.save_correlation(subtype, obj_id, date_range)
    #     if res and 'tags' in obj_meta:
    #         # # TODO: handle mixed tags: taxonomies and Galaxies
    #         pass
    #         #Tag.api_add_obj_tags(tags=obj_meta['tags'], object_id=obj_id, object_type=self.get_correlation_obj_type())
    #     return True
    #
    # # # TODO: handle tags
    # def delete_correlation(self, obj_id):
    #     pass


######## API EXPOSED ########


########  ########

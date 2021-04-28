#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import item_basic

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
import Date
#import Tag

config_loader = ConfigLoader.ConfigLoader()
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
config_loader = None

def get_all_correlation_objects():
    '''
    Return a list of all correllated objects
    '''
    return ['domain', 'paste']

class Correlation(object):

    def __init__(self, correlation_name, all_correlation_types):
        self.correlation_name = correlation_name
        self.all_correlation_types = all_correlation_types

    def _exist_corelation_field(self, correlation_type, field_name, item_type='paste'):
        if item_type=='paste':
            return r_serv_metadata.exists('set_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))
        else:
            return r_serv_metadata.exists('set_domain_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))

    def exist_correlation(self, subtype, obj_id):
        res = r_serv_metadata.zscore('{}_all:{}'.format(self.correlation_name, subtype), obj_id)
        if res is not None:
            return True
        else:
            return False

    def _get_items(self, correlation_type, field_name):
        res =  r_serv_metadata.smembers('set_{}_{}:{}'.format(self.correlation_name, correlation_type, field_name))
        if res:
            return list(res)
        else:
            return []

    def get_correlation_first_seen(self, subtype, obj_id, r_int=False):
        res = r_serv_metadata.hget('{}_metadata_{}:{}'.format(self.correlation_name, subtype, obj_id), 'first_seen')
        if r_int:
            if res:
                return int(res)
            else:
                return 99999999
        else:
            return res

    def get_correlation_last_seen(self, subtype, obj_id, r_int=False):
        res = r_serv_metadata.hget('{}_metadata_{}:{}'.format(self.correlation_name, subtype, obj_id), 'last_seen')
        if r_int:
            if res:
                return int(res)
            else:
                return 0
        else:
            return res

    def _get_metadata(self, subtype, obj_id):
        meta_dict = {}
        meta_dict['first_seen'] = self.get_correlation_first_seen(subtype, obj_id)
        meta_dict['last_seen'] = self.get_correlation_last_seen(subtype, obj_id)
        meta_dict['nb_seen'] = r_serv_metadata.scard('set_{}_{}:{}'.format(self.correlation_name, subtype, obj_id))
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

    def get_all_correlations_by_subtype(self, subtype):
        return r_serv_metadata.zrange(f'{self.correlation_name}_all:{subtype}', 0, -1)

    def get_all_correlations_by_subtype_pagination(self, subtype, nb_elem=50, page=1):
        start = (page - 1) * nb_elem
        stop = start + nb_elem -1
        return r_serv_metadata.zrange(f'{self.correlation_name}_all:{subtype}', start, stop)

    def paginate_list(self, obj_list, nb_elem=50, page=1):
        start = (page - 1) * nb_elem
        stop = start + nb_elem
        return obj_list[start:stop]

    def get_all_correlation_types(self):
        '''
        Gel all correlation types

        :return: A list of all the correlation types
        :rtype: list
        '''
        return self.all_correlation_types

    def is_valid_obj_subtype(self, subtype):
        if subtype in self.all_correlation_types:
            return True
        else:
            return False

    def get_correlation_obj_type(self):
        if self.correlation_name=='pgpdump':
            return 'pgp'
        else:
            return 'cryptocurrency'

    def sanythise_correlation_types(self, correlation_types, r_boolean=False):
        '''
        Check if all correlation types in the list are valid.

        :param correlation_types: list of correlation type
        :type currency_type: list

        :return: If a type is invalid, return the full list of correlation types else return the provided list
        :rtype: list
        '''
        if correlation_types is None:
            if r_boolean:
                return False
            else:
                return self.get_all_correlation_types()
        for correl in correlation_types: # # TODO: # OPTIMIZE:
            if correl not in self.get_all_correlation_types():
                if r_boolean:
                    return False
                else:
                    return self.get_all_correlation_types()
        if r_boolean:
            return True
        else:
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
        if not correlation_objects:
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

    def update_correlation_daterange(self, subtype, obj_id, date):
        date = int(date)
        # obj_id don't exit
        if not r_serv_metadata.exists('{}_metadata_{}:{}'.format(self.correlation_name, subtype, obj_id)):
            r_serv_metadata.hset('{}_metadata_{}:{}'.format(self.correlation_name, subtype, obj_id), 'first_seen', date)
            r_serv_metadata.hset('{}_metadata_{}:{}'.format(self.correlation_name, subtype, obj_id), 'last_seen', date)
        else:
            first_seen = self.get_correlation_last_seen(subtype, obj_id, r_int=True)
            last_seen = self.get_correlation_first_seen(subtype, obj_id, r_int=True)
            if date < first_seen:
                r_serv_metadata.hset('{}_metadata_{}:{}'.format(self.correlation_name, subtype, obj_id), 'first_seen', date)
            if date > last_seen:
                r_serv_metadata.hset('{}_metadata_{}:{}'.format(self.correlation_name, subtype, obj_id), 'last_seen', date)

    def save_item_correlation(self, subtype, obj_id, item_id, item_date):
        self.update_correlation_daterange(subtype, obj_id, item_date)

        # global set
        r_serv_metadata.sadd('set_{}_{}:{}'.format(self.correlation_name, subtype, obj_id), item_id)

        # daily
        r_serv_metadata.hincrby('{}:{}:{}'.format(self.correlation_name, subtype, item_date), obj_id, 1)

        # all type
        r_serv_metadata.zincrby('{}_all:{}'.format(self.correlation_name, subtype), obj_id, 1)

        ## object_metadata
        # item
        r_serv_metadata.sadd('item_{}_{}:{}'.format(self.correlation_name, subtype, item_id), obj_id)

        # domain
        if item_basic.is_crawled(item_id):
            domain = item_basic.get_item_domain(item_id)
            self.save_domain_correlation(domain, subtype, obj_id)

    def delete_item_correlation(self, subtype, obj_id, item_id, item_date):
        #self.update_correlation_daterange(subtype, obj_id, item_date) update daterange ! # # TODO:
        r_serv_metadata.srem('set_{}_{}:{}'.format(self.correlation_name, subtype, obj_id), item_id)
        r_serv_metadata.srem('item_{}_{}:{}'.format(self.correlation_name, subtype, item_id), obj_id)

        res = r_serv_metadata.hincrby('{}:{}:{}'.format(self.correlation_name, subtype, item_date), obj_id, -1)
        if int(res) < 0: # remove last
            r_serv_metadata.hdel('{}:{}:{}'.format(self.correlation_name, subtype, item_date), obj_id)

        res = r_serv_metadata.zscore('{}_all:{}'.format(self.correlation_name, subtype), obj_id)
        if int(res) > 0:
            r_serv_metadata.zincrby('{}_all:{}'.format(self.correlation_name, subtype), obj_id, -1)

    def save_domain_correlation(self, domain, subtype, obj_id):
        r_serv_metadata.sadd('domain_{}_{}:{}'.format(self.correlation_name, subtype, domain), obj_id)
        r_serv_metadata.sadd('set_domain_{}_{}:{}'.format(self.correlation_name, subtype, obj_id), domain)

    def delete_domain_correlation(self, domain, subtype, obj_id):
        r_serv_metadata.srem('domain_{}_{}:{}'.format(self.correlation_name, subtype, domain), obj_id)
        r_serv_metadata.srem('set_domain_{}_{}:{}'.format(self.correlation_name, subtype, obj_id), domain)

    def save_correlation(self, subtype, obj_id, date_range):
        r_serv_metadata.zincrby('{}_all:{}'.format(self.correlation_name, subtype), obj_id, 0)
        self.update_correlation_daterange(subtype, obj_id, date_range['date_from'])
        if date_range['date_from'] != date_range['date_to']:
            self.update_correlation_daterange(subtype, obj_id, date_range['date_to'])
        return True

    def save_obj_relationship(self, subtype, obj_id, obj2_type, obj2_id):
        if obj2_type == 'domain':
            self.save_domain_correlation(obj2_id, subtype, obj_id)
        elif obj2_type == 'item':
            self.save_item_correlation(subtype, obj_id, obj2_id, item_basic.get_item_date(obj2_id))

    def delete_obj_relationship(self, subtype, obj_id, obj2_type, obj2_id):
        if obj2_type == 'domain':
            self.delete_domain_correlation(obj2_id, subtype, obj_id)
        elif obj2_type == 'item':
            self.delete_item_correlation(subtype, obj_id, obj2_id, item_basic.get_item_date(obj2_id))

    def create_correlation(self, subtype, obj_id, obj_meta):
        res = self.sanythise_correlation_types([subtype], r_boolean=True)
        if not res:
            print('invalid subtype')
            return False
        first_seen = obj_meta.get('first_seen', None)
        last_seen = obj_meta.get('last_seen', None)
        date_range = Date.sanitise_date_range(first_seen, last_seen, separator='', date_type='datetime')
        res = self.save_correlation(subtype, obj_id, date_range)
        if res and 'tags' in obj_meta:
            # # TODO: handle mixed tags: taxonomies and Galaxies
            pass
            #Tag.api_add_obj_tags(tags=obj_meta['tags'], object_id=obj_id, object_type=self.get_correlation_obj_type())
        return True

    # # TODO: handle tags
    def delete_correlation(self, subtype, obj_id):
        res = self.sanythise_correlation_types([subtype], r_boolean=True)
        if not res:
            print('invalid subtype')
            return False
        if not self.exist_correlation(subtype, obj_id):
            return False

        obj_correlations = self.get_correlation_all_object(subtype, obj_id)
        if 'domain' in obj_correlations:
            for domain in obj_correlations['domain']:
                r_serv_metadata.srem('domain_{}_{}:{}'.format(self.correlation_name, subtype, domain), obj_id)
            r_serv_metadata.delete('set_domain_{}_{}:{}'.format(self.correlation_name, subtype, obj_id))


        if 'paste' in obj_correlations: # TODO: handle item
            for item_id in obj_correlations['paste']:

                r_serv_metadata.srem('item_{}_{}:{}'.format(self.correlation_name, subtype, item_id), obj_id)
            r_serv_metadata.delete('set_{}_{}:{}'.format(self.correlation_name, subtype, obj_id))

            # delete daily correlation
            first_seen = self.get_correlation_first_seen(subtype, obj_id)
            last_seen = self.get_correlation_last_seen(subtype, obj_id)
            meta_date = Date.sanitise_date_range(first_seen, last_seen)
            date_range = Date.substract_date(meta_date['date_from'], meta_date['date_to'])
            for date_day in date_range:
                r_serv_metadata.hdel('{}:{}:{}'.format(self.correlation_name, subtype, date_day), obj_id)

        r_serv_metadata.delete('{}_metadata_{}:{}'.format(self.correlation_name, subtype, obj_id))
        r_serv_metadata.zrem('{}_all:{}'.format(self.correlation_name, subtype), obj_id)

        return True

    ######## API EXPOSED ########
    def api_check_objs_type(self, l_types):
        for obj_type in l_types:
            if not self.is_valid_obj_subtype(obj_type):
                return ({"error": f"Invalid Type: {obj_type}"}, 400)

    ########  ########

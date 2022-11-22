#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis

from flask import url_for

sys.path.append(os.environ['AIL_BIN'])
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, get_all_id

config_loader = ConfigLoader()

config_loader = None

class CryptoCurrency(AbstractSubtypeObject):
    """
    AIL CryptoCurrency Object. (strings)
    """

    def __init__(self, id, subtype):
        super(CryptoCurrency, self).__init__('cryptocurrency', id, subtype=subtype)

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True),
    #                 'compress': 'gzip'}
    #     return payload

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    def get_currency_symbol(self):
        if self.subtype=='bitcoin':
            return 'BTC'
        elif self.subtype=='ethereum':
            return 'ETH'
        elif self.subtype=='bitcoin-cash':
            return 'BCH'
        elif self.subtype=='litecoin':
            return 'LTC'
        elif self.subtype=='monero':
            return 'XMR'
        elif self.subtype=='zcash':
            return 'ZEC'
        elif self.subtype=='dash':
            return 'DASH'
        return None

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, subtype=self.subtype, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&subtype={self.subtype}&id={self.id}'
        return url

    def get_svg_icon(self):
        if self.subtype == 'bitcoin':
            style = 'fab'
            icon = '\uf15a'
        elif self.subtype == 'monero':
            style = 'fab'
            icon = '\uf3d0'
        elif self.subtype == 'ethereum':
            style = 'fab'
            icon = '\uf42e'
        else:
            style = 'fas'
            icon = '\uf51e'
        return {'style': style, 'icon': icon, 'color': '#DDCC77', 'radius':5}

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('coin-address')
        obj.first_seen = self.get_first_seen()
        obj.last_seen = self.get_last_seen()

        obj_attrs.append( obj.add_attribute('address', value=self.id) )
        crypto_symbol = self.get_currency_symbol()
        if crypto_symbol:
            obj_attrs.append( obj.add_attribute('symbol', value=crypto_symbol) )

        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_meta(self, options=set()):
        meta = self._get_meta()
        meta['id'] = self.id
        meta['subtype'] = self.subtype
        meta['tags'] = self.get_tags(r_list=True)
        return meta



    ############################################################################
    ############################################################################

def get_all_subtypes():
    #return ail_core.get_object_all_subtypes(self.type)
    return ['bitcoin', 'bitcoin-cash', 'dash', 'ethereum', 'litecoin', 'monero', 'zcash']

# def build_crypto_regex(subtype, search_id):
#     pass
#
# def search_by_name(subtype, search_id): ##################################################
#
#     # # TODO: BUILD regex
#     obj = CryptoCurrency(subtype, search_id)
#     if obj.exists():
#         return search_id
#     else:
#         regex = build_crypto_regex(subtype, search_id)
#         return abstract_object.search_subtype_obj_by_id('cryptocurrency', subtype, regex)





# by days -> need first/last entry USEFULL FOR DATA RETENTION UI

def get_all_cryptocurrencies():
    cryptos = {}
    for subtype in get_all_subtypes():
        cryptos[subtype] = get_all_cryptocurrencies_by_subtype(subtype)
    return cryptos

def get_all_cryptocurrencies_by_subtype(subtype):
    return get_all_id('cryptocurrency', subtype)

if __name__ == '__main__':
    res = get_all_cryptocurrencies()
    print(res)

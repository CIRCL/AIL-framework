#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys

from flask import url_for
from hashlib import sha256

from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_subtype_object import AbstractSubtypeObject, AbstractSubtypeObjects, get_all_id

config_loader = ConfigLoader()
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None

digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
digits58_ripple = 'rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz'
digits32 = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'


def decode_bech32(address):
    if not all(33 <= ord(x) <= 126 for x in address):
        return None, None
    address = address.lower()
    pos = address.rfind('1')
    if pos < 1 or pos + 7 > len(address):
        return None, None
    hrp = address[:pos]
    data = address[pos+1:]
    if not all(x in digits32 for x in data):
        return None, None
    data = [digits32.find(c) for c in data]
    # if not verify_checksum(hrp, data): # TODO checksum ???
    #     return None, None
    return hrp, data[:-6]

def check_bech32_address(address):
    hrp, data = decode_bech32(address)
    if hrp is None or data is None:
        return False
    if hrp != 'bc' and hrp != 'tb':
        return False
    return True

# http://rosettacode.org/wiki/Bitcoin/address_validation#Python
def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return n.to_bytes(length, 'big')

# http://rosettacode.org/wiki/Bitcoin/address_validation#Python
def check_base58_address(bc):
    try:
        bcbytes = decode_base58(bc, 25)
        return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]
    except Exception:
        return False

def decode_base58_ripple(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58_ripple.index(char)
    return n.to_bytes(length, 'big')

def check_base58_ripple_address(bc):
    try:
        bcbytes = decode_base58_ripple(bc, 25)
        return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]
    except Exception:
        return False


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

    def is_valid_address(self):
        if self.subtype == 'bitcoin':
            if self.id.startswith('bc'):
                if check_bech32_address(self.id):
                    return True
            return check_base58_address(self.id)
        elif self.subtype == 'dash' or self.subtype == 'litecoin' or self.subtype == 'tron':
            return check_base58_address(self.id)
        elif self.subtype == 'ripple':
            return check_base58_ripple_address(self.id)
        else:
            return True

    def get_currency_symbol(self):
        if self.subtype == 'bitcoin':
            return 'BTC'
        elif self.subtype == 'ethereum':
            return 'ETH'
        elif self.subtype == 'bitcoin-cash':
            return 'BCH'
        elif self.subtype == 'litecoin':
            return 'LTC'
        elif self.subtype == 'monero':
            return 'XMR'
        elif self.subtype == 'zcash':
            return 'ZEC'
        elif self.subtype == 'dash':
            return 'DASH'
        elif self.subtype == 'ripple':
            return 'XRP'
        elif self.subtype == 'tron':
            return 'TRX'
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
        return {'style': style, 'icon': icon, 'color': '#DDCC77', 'radius': 5}

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('coin-address')
        first_seen = self.get_first_seen()
        last_seen = self.get_last_seen()
        if first_seen:
            obj.first_seen = first_seen
        if last_seen:
            obj.last_seen = last_seen
        if not first_seen or not last_seen:
            self.logger.warning(
                f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={first_seen}, last={last_seen}')

        obj_attrs.append(obj.add_attribute('address', value=self.id))
        crypto_symbol = self.get_currency_symbol()
        if crypto_symbol:
            obj_attrs.append(obj.add_attribute('symbol', value=crypto_symbol))

        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['subtype'] = self.subtype
        meta['tags'] = self.get_tags(r_list=True)
        return meta


class CryptoCurrencies(AbstractSubtypeObjects):
    """
        Usernames Objects
    """
    def __init__(self):
        super().__init__('cryptocurrency', CryptoCurrency)

    def get_name(self):
        return 'Cryptocurrencies'

    def get_icon(self):
        return {'fas': 'fas', 'icon': 'coins'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_subtypes.objects_dashboard_cryptocurrency')
        else:
            url = f'{baseurl}/objects/cryptocurrencies'
        return url

    def sanitize_id_to_search(self, subtypes, name_to_search):
        return name_to_search


    ############################################################################
    ############################################################################


def get_all_subtypes():
    # return ail_core.get_object_all_subtypes(self.type)
    return ['bitcoin', 'bitcoin-cash', 'dash', 'ethereum', 'litecoin', 'monero', 'ripple', 'tron', 'zcash']


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


def get_subtype_by_symbol(symbol):
    if symbol == 'BTC':
        return 'bitcoin'
    elif symbol == 'ETH':
        return 'ethereum'
    elif symbol == 'BCH':
        return 'bitcoin-cash'
    elif symbol == 'LTC':
        return 'litecoin'
    elif symbol == 'XMR':
        return 'monero'
    elif symbol == 'ZEC':
        return 'zcash'
    elif symbol == 'DASH':
        return 'dash'
    elif symbol == 'XRP':
        return 'ripple'
    elif symbol == 'TRX':
        return 'tron'
    return None


# by days -> need first/last entry USEFUL FOR DATA RETENTION UI

def get_all_cryptocurrencies():
    cryptos = {}
    for subtype in get_all_subtypes():
        cryptos[subtype] = get_all_cryptocurrencies_by_subtype(subtype)
    return cryptos

def get_all_cryptocurrencies_by_subtype(subtype):
    return get_all_id('cryptocurrency', subtype)

def sanitize_cryptocurrency_name_to_search(name_to_search, subtype): # TODO FILTER NAME + Key + mail
    if subtype == '':
        pass
    return name_to_search

def search_cryptocurrency_by_name(name_to_search, subtype, r_pos=False):
    cryptocurrencies = {}
    # for subtype in subtypes:
    r_name = sanitize_cryptocurrency_name_to_search(name_to_search, subtype)
    if not name_to_search or isinstance(r_name, dict):
        # break
        return cryptocurrencies
    r_name = re.compile(r_name)
    for crypto_name in get_all_cryptocurrencies_by_subtype(subtype):
        res = re.search(r_name, crypto_name)
        if res:
            cryptocurrencies[crypto_name] = {}
            if r_pos:
                cryptocurrencies[crypto_name]['hl-start'] = res.start()
                cryptocurrencies[crypto_name]['hl-end'] = res.end()
    return cryptocurrencies


# # TODO save object
# def import_misp_object(misp_obj):
#     """
#     :type misp_obj: MISPObject
#     """
#     obj_id = None
#     obj_subtype = None
#     for attribute in misp_obj.attributes:
#         if attribute.object_relation == 'address':  # TODO: handle xmr address field
#             obj_id = attribute.value
#         elif attribute.object_relation == 'symbol':
#             obj_subtype = get_subtype_by_symbol(attribute.value)
#     if obj_id and obj_subtype:
#         obj = CryptoCurrency(obj_id, obj_subtype)
#         first_seen, last_seen = obj.get_misp_object_first_last_seen(misp_obj)
#         tags = obj.get_misp_object_tags(misp_obj)
#         # for tag in tags:
#         #     obj.add_tag()


# if __name__ == '__main__':
#     name_to_search = '3c'
#     subtype = 'bitcoin'
#     print(search_cryptocurrency_by_name(name_to_search, subtype))

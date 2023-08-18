#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import cld3
import html2text

from datetime import datetime

from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ail_core import get_ail_uuid
from lib.objects.abstract_object import AbstractObject
from lib.ConfigLoader import ConfigLoader
from lib.data_retention_engine import update_obj_date, get_obj_date_first
# TODO Set all messages ???


from flask import url_for

config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
r_content = config_loader.get_db_conn("Kvrocks_Content")
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


# TODO SAVE OR EXTRACT MESSAGE SOURCE FOR ICON ?????????
# TODO iterate on all objects
# TODO also add support for small objects ????

# CAN Message exists without CHAT -> no convert it to object

# ID:   source:chat_id:message_id ????
#
# /!\ handle null chat and message id -> chat = uuid and message = timestamp ???


class Message(AbstractObject):
    """
    AIL Message Object. (strings)
    """

    def __init__(self, id):  # TODO subtype or use source ????
        super(Message, self).__init__('message', id)  # message::< telegram/1692189934.380827/ChatID_MessageID >

    def exists(self):
        if self.subtype is None:
            return r_object.exists(f'meta:{self.type}:{self.id}')
        else:
            return r_object.exists(f'meta:{self.type}:{self.get_subtype(r_str=True)}:{self.id}')

    def get_source(self):
        """
        Returns source/feeder name
        """
        l_source = self.id.split('/')[:-4]
        return os.path.join(*l_source)

    def get_basename(self):
        return os.path.basename(self.id)

    def get_content(self, r_type='str'): # TODO ADD cache # TODO Compress content ???????
        """
        Returns content
        """
        content = self._get_field('content')
        if r_type == 'str':
            return content
        elif r_type == 'bytes':
            return content.encode()

    def get_date(self):
        timestamp = self.get_timestamp()
        return datetime.fromtimestamp(timestamp).strftime('%Y%m%d')

    def get_timestamp(self):
        dirs = self.id.split('/')
        return dirs[-2]

    def get_message_id(self):  # TODO optimize
        message_id = self.get_basename().rsplit('_', 1)[1]
        # if message_id.endswith('.gz'):
        #     message_id = message_id[:-3]
        return message_id

    def get_chat_id(self):  # TODO optimize
        chat_id =  self.get_basename().rsplit('_', 1)[0]
        # if chat_id.endswith('.gz'):
        #     chat_id = chat_id[:-3]
        return chat_id

    # Update value on import
    # reply to -> parent ?
    # reply/comment - > children ?
    # nb views
    # reactions
    # nb fowards
    # room ???
    # message from channel ???
    # message media

    def get_translation(self):  # TODO support multiple translated languages ?????
        """
        Returns translated content
        """
        return self._get_field('translated')  # TODO multiples translation ... -> use set

    def _set_translation(self, translation):
        """
        Set translated content
        """
        return self._set_field('translated', translation)  # translation by hash ??? -> avoid translating multiple time

    def get_html2text_content(self, content=None, ignore_links=False):
        if not content:
            content = self.get_content()
        h = html2text.HTML2Text()
        h.ignore_links = ignore_links
        h.ignore_images = ignore_links
        return h.handle(content)

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True)}
    #     return payload

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': 'fa-comment-dots', 'color': '#4dffff', 'radius': 5}

    def get_misp_object(self):  # TODO
        obj = MISPObject('instant-message', standalone=True)
        obj_date = self.get_date()
        if obj_date:
            obj.first_seen = obj_date
        else:
            self.logger.warning(
                f'Export error, None seen {self.type}:{self.subtype}:{self.id}, first={obj_date}')

        # obj_attrs = [obj.add_attribute('first-seen', value=obj_date),
        #              obj.add_attribute('raw-data', value=self.id, data=self.get_raw_content()),
        #              obj.add_attribute('sensor', value=get_ail_uuid())]
        obj_attrs = []
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    # def get_url(self):
    #     return r_object.hget(f'meta:item::{self.id}', 'url')

    # options: set of optional meta fields
    def get_meta(self, options=None):
        """
        :type options: set
        """
        if options is None:
            options = set()
        meta = self.get_default_meta(tags=True)
        meta['date'] = self.get_date() # TODO replace me by timestamp ??????
        meta['source'] = self.get_source()
        # optional meta fields
        if 'content' in options:
            meta['content'] = self.get_content()
        if 'parent' in options:
            meta['parent'] = self.get_parent()
        if 'investigations' in options:
            meta['investigations'] = self.get_investigations()
        if 'link' in options:
            meta['link'] = self.get_link(flask_context=True)

        # meta['encoding'] = None
        return meta

    def _languages_cleaner(self, content=None):
        if not content:
            content = self.get_content()
        # REMOVE URLS
        regex = r'\b(?:http://|https://)?(?:[a-zA-Z\d-]{,63}(?:\.[a-zA-Z\d-]{,63})+)(?:\:[0-9]+)*(?:/(?:$|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*\b'
        url_regex = re.compile(regex)
        urls = url_regex.findall(content)
        urls = sorted(urls, key=len, reverse=True)
        for url in urls:
            content = content.replace(url, '')
        # REMOVE PGP Blocks
        regex_pgp_public_blocs = r'-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]+?-----END PGP PUBLIC KEY BLOCK-----'
        regex_pgp_signature = r'-----BEGIN PGP SIGNATURE-----[\s\S]+?-----END PGP SIGNATURE-----'
        regex_pgp_message = r'-----BEGIN PGP MESSAGE-----[\s\S]+?-----END PGP MESSAGE-----'
        re.compile(regex_pgp_public_blocs)
        re.compile(regex_pgp_signature)
        re.compile(regex_pgp_message)
        res = re.findall(regex_pgp_public_blocs, content)
        for it in res:
            content = content.replace(it, '')
        res = re.findall(regex_pgp_signature, content)
        for it in res:
            content = content.replace(it, '')
        res = re.findall(regex_pgp_message, content)
        for it in res:
            content = content.replace(it, '')
        return content

    def detect_languages(self, min_len=600, num_langs=3, min_proportion=0.2, min_probability=0.7):
        languages = []
        ## CLEAN CONTENT ##
        content = self.get_html2text_content(ignore_links=True)
        content = self._languages_cleaner(content=content)
        # REMOVE USELESS SPACE
        content = ' '.join(content.split())
        # - CLEAN CONTENT - #
        if len(content) >= min_len:
            for lang in cld3.get_frequent_languages(content, num_langs=num_langs):
                if lang.proportion >= min_proportion and lang.probability >= min_probability and lang.is_reliable:
                    languages.append(lang)
        return languages

    # def translate(self, content=None): # TODO translation plugin
    #     # TODO get text language
    #     if not content:
    #         content = self.get_content()
    #     translated = argostranslate.translate.translate(content, 'ru', 'en')
    #     # Save translation
    #     self._set_translation(translated)
    #     return translated

    def create(self, content, translation, tags):
        self._set_field('content', content)
        r_content.get(f'content:{self.type}:{self.get_subtype(r_str=True)}:{self.id}', content)
        if translation:
            self._set_translation(translation)
        for tag in tags:
            self.add_tag(tag)

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        pass

def create_obj_id(source, chat_id, message_id, timestamp):
    return f'{source}/{timestamp}/{chat_id}_{message_id}'

# TODO Check if already exists
# def create(source, chat_id, message_id, timestamp, content, tags=[]):
def create(obj_id, content, translation=None, tags=[]):
    message = Message(obj_id)
    if not message.exists():
        message.create(content, translation, tags)
    return message


# TODO Encode translation


if __name__ == '__main__':
    r = 'test'
    print(r)

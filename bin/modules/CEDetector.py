#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Onion Module
============================

This module extract url from item and returning only ones which are tor
related (.onion). All These urls are send to the crawler discovery queue.

Requirements
------------

*Need running Redis instances. (Redis)

"""
import os
import sys

from textblob import TextBlob
from nltk.tokenize import RegexpTokenizer

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader

class CEDetector(AbstractModule):
    """docstring for Onion module."""

    def __init__(self, queue=True):
        super(CEDetector, self).__init__(queue=queue)

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Cache")

        self.csam_words = self.load_world_file('csam_words')
        self.child_worlds = self.load_world_file('child_words')
        self.porn_worlds = self.load_world_file('porn_words')

        self.ce_tag = 'dark-web:topic="pornography-child-exploitation"'
        self.tokenizer = RegexpTokenizer('[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\//\=\'\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]+',
                                         gaps=True, discard_empty=True)

    def load_world_file(self, path):
        words = set()
        try:
            with open(os.path.join(os.environ['AIL_HOME'], f'files/{path}')) as f:
                content = f.read()
        except FileNotFoundError:
            content = ''
        content = content.splitlines()
        for line in content:
            if line.startswith('#') or not line:
                continue
            word = line.split()
            if word:
                words.add(word[0])
        return words

    def compute(self, message):  # TODO LIMIT TO DARKWEB ???
        to_tag = False
        content = self.obj.get_content().lower()
        # print(content)

        is_csam = False
        is_child_word = False
        is_porn_world = False
        words = TextBlob(content, tokenizer=self.tokenizer).tokens
        words = set(words)

        for word in words:
            if word in self.csam_words:
                is_csam = True
            if word in self.child_worlds:
                is_child_word = True
            if word in self.porn_worlds:
                is_porn_world = True
            # PERF ???
            # if is_child_word and is_porn_world:
            #     break

        if is_csam:
            to_tag = True
        if is_child_word and is_porn_world:
            to_tag = True

        if to_tag:
            # print(f'{content}                         DETECTED')
            # print()
            self.add_message_to_queue(message=self.ce_tag, queue='Tags')

        return to_tag

def test_detection():
    from lib import Tag
    from lib.objects.Domains import Domain
    from lib.objects.Titles import Title

    not_detected = set()
    tag = 'dark-web:topic="pornography-child-exploitation"'
    tag_key = f'domain::{tag}'
    for domain in Tag.get_obj_by_tag(tag_key):
        dom = Domain(domain)
        is_detected = False
        for h in dom.get_correlation('title').get('title', []):
            module.obj = Title(h[1:])
            if module.compute(''):
                is_detected = True
        if not is_detected:
            not_detected.add(domain)

    print()
    print()
    print()
    print()
    for domain in not_detected:
        dom = Domain(domain)
        print('-----------', domain)
        for h in dom.get_correlation('title').get('title', []):
            print(Title(h[1:]).get_content().lower())
        print()
        print()


if __name__ == "__main__":
    module = CEDetector()
    module.run()
    # test_detection()

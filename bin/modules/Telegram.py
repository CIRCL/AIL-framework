#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Telegram Module
============================

Search telegram username,channel and invite code

"""
import os
import re
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from packages.Item import Item
from lib import regex_helper
from lib import telegram

class Telegram(AbstractModule):
    """Telegram module for AIL framework"""

    def __init__(self):
        super(Telegram, self).__init__()

        # https://github.com/LonamiWebs/Telethon/wiki/Special-links
        self.re_telegram_link = r'(telegram\.me|t\.me|telegram\.dog|telesco\.pe)/([^\.\",\s]+)'
        self.re_tg_link = r'tg://.+'

        re.compile(self.re_telegram_link)
        re.compile(self.re_tg_link)

        self.redis_cache_key = regex_helper.generate_redis_cache_key(self.module_name)
        self.max_execution_time = 60

        # Send module state to logs
        self.redis_logger.info(f"Module {self.module_name} initialized")

    def compute(self, message, r_result=False):
        # messsage = item_id
        item = Item(message)
        item_content = item.get_content()
        item_date = item.get_date()

        invite_code_found = False

        # extract telegram links
        telegram_links = self.regex_findall(self.re_telegram_link, item.get_id(), item_content)
        for telegram_link_tuple in telegram_links:
            print(telegram_link_tuple)
            print(telegram_link_tuple[2:-2].split("', '", 1))
            base_url, url_path = telegram_link_tuple[2:-2].split("', '", 1)
            dict_url = telegram.get_data_from_telegram_url(base_url, url_path)
            if dict_url.get('username'):
                telegram.save_item_correlation(dict_url['username'], item.get_id(), item_date)
                print(f'username: {dict_url["username"]}')
            if dict_url.get('invite_hash'):
                telegram.save_telegram_invite_hash(dict_url['invite_hash'], item.get_id())
                print(f'invite code: {dict_url["invite_hash"]}')
                invite_code_found = True

        # extract tg links
        tg_links = self.regex_findall(self.re_tg_link, item.get_id(), item_content)
        for tg_link in tg_links:
            dict_url = telegram.get_data_from_tg_url(tg_link)
            if dict_url.get('username'):
                telegram.save_item_correlation(dict_url['username'], item.get_id(), item_date)
                print(f'username: {dict_url["username"]}')
            if dict_url.get('invite_hash'):
                telegram.save_telegram_invite_hash(dict_url['invite_hash'], item.get_id())
                print(f'invite code: {dict_url["invite_hash"]}')
                invite_code_found = True
            if dict_url.get('login_code'):
                print(f'login code: {dict_url["login_code"]}')

        # CREATE TAG
        if invite_code_found:
            #tags
            msg = f'infoleak:automatic-detection="telegram-invite-hash";{item.get_id()}'
            self.send_message_to_queue(msg, 'Tags')


if __name__ == "__main__":
    module = Telegram()
    module.run()

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
from lib.objects.Items import Item
from lib.objects.Usernames import Username
from lib import regex_helper
from lib import telegram

class Telegram(AbstractModule):
    """Telegram module for AIL framework"""

    def __init__(self):
        super(Telegram, self).__init__()

        # https://github.com/LonamiWebs/Telethon/wiki/Special-links
        self.re_telegram_link = r'(telegram\.me|t\.me|telegram\.dog|telesco\.pe)/(\w+)'
        self.re_tg_link = r'tg://.+'

        re.compile(self.re_telegram_link)
        re.compile(self.re_tg_link)

        self.redis_cache_key = regex_helper.generate_redis_cache_key(self.module_name)
        self.max_execution_time = 60

        # Send module state to logs
        self.logger.info(f"Module {self.module_name} initialized")

    def compute(self, message, r_result=False):
        item = self.get_obj()
        item_content = item.get_content()
        item_date = item.get_date()

        invite_code_found = False

        # extract telegram links
        telegram_links = self.regex_findall(self.re_telegram_link, item.get_id(), item_content)
        telegram_links = set(telegram_links)
        for telegram_link_tuple in telegram_links:
            # print(telegram_link_tuple)
            # print(telegram_link_tuple[2:-2].split("', '", 1))
            base_url, url_path = telegram_link_tuple[2:-2].split("', '", 1)
            dict_url = telegram.get_data_from_telegram_url(base_url, url_path)
            user_id = dict_url.get('username')
            if user_id:
                username = Username(user_id, 'telegram')
                username.add(item_date, item)
                print(f'username: {user_id}')
            invite_hash = dict_url.get('invite_hash')
            if invite_hash:
                telegram.save_telegram_invite_hash(invite_hash, self.obj.get_global_id())
                print(f'invite code: {invite_hash}')
                invite_code_found = True

        # extract tg links
        tg_links = self.regex_findall(self.re_tg_link, item.get_id(), item_content)
        for tg_link in tg_links:
            dict_url = telegram.get_data_from_tg_url(tg_link)
            user_id = dict_url.get('username')
            if user_id:
                username = Username(user_id, 'telegram')
                username.add(item_date, item)
                print(f'username: {user_id}')
            invite_hash = dict_url.get('invite_hash')
            if invite_hash:
                telegram.save_telegram_invite_hash(invite_hash, item.get_id())
                print(f'invite code: {invite_hash}')
                invite_code_found = True
            if dict_url.get('login_code'):
                print(f'login code: {dict_url["login_code"]}')

        # CREATE TAG
        if invite_code_found:
            # tags
            tag = 'infoleak:automatic-detection="telegram-invite-hash"'
            self.add_message_to_queue(message=tag, queue='Tags')


if __name__ == "__main__":
    module = Telegram()
    module.run()

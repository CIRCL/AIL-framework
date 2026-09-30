#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Telegram Feeder Importer Module
================

Process Telegram JSON

"""
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer.feeders.abstract_chats_feeder import AbstractChatFeeder

class Rocket_ChatFeeder(AbstractChatFeeder):

    def __init__(self, json_data):
        super().__init__('rocket-chat', json_data)

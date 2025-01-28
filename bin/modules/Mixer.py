#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Mixer Module
================

This module is consuming the Redis-list created by the ZMQ_Feed_Q Module.

This module take all the feeds provided in the config.


Depending on the configuration, this module will process the feed as follows:
    operation_mode 1: "Avoid any duplicate from any sources"
        - The module maintain a list of content for each item
            - If the content is new, process it
            - Else, do not process it but keep track for statistics on duplicate

    DISABLED
    operation_mode 2: "Keep duplicate coming from different sources"
        - The module maintain a list of name given to the item by the feeder
            - If the name has not yet been seen, process it
            - Elseif, the saved content associated with the item is not the same, process it
            - Else, do not process it but keep track for statistics on duplicate

    operation_mode 3: "Don't look if duplicated content"
        - SImply do not bother to check if it is a duplicate
        - Simply do not bother to check if it is a duplicate

Note that the hash of the content is defined as the sha1(gzip64encoded).

"""
import os
import sys
import time

# import hashlib

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader
from lib import ail_stats


class Mixer(AbstractModule):
    """docstring for Mixer module."""

    def __init__(self):
        super(Mixer, self).__init__()

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Mixer_Cache")

        self.pending_seconds = 1

        self.refresh_time = 30
        timestamp = int(time.time())
        self.last_refresh = int(timestamp - (timestamp % 30))
        if timestamp > self.last_refresh:
            self.last_refresh += 30

        self.operation_mode = config_loader.get_config_int("Module_Mixer", "operation_mode")
        print(f'Operation mode {self.operation_mode}')

        self.ttl_key = config_loader.get_config_int("Module_Mixer", "ttl_duplicate")
        self.default_feeder_name = config_loader.get_config_str("Module_Mixer", "default_unnamed_feed_name")

        self.feeders_processed = {}

        self.logger.info(f"Module: {self.module_name} Launched")

    def increase_stat_processed(self, feeder):
        try:
            self.feeders_processed[feeder] += 1
        except KeyError:
            self.feeders_processed[feeder] = 1

    def refresh_stats(self):
        timestamp = int(time.time())
        if timestamp >= self.last_refresh:
            timestamp = timestamp - timestamp % self.refresh_time
            print('update', timestamp)
            print(self.feeders_processed)
            ail_stats.add_feeders(timestamp, self.feeders_processed)
            self.feeders_processed = {}
            self.last_refresh = self.last_refresh + 30

    def computeNone(self):
        self.refresh_stats()

    def compute(self, message):
        self.refresh_stats()
        # obj = self.obj
        # TODO CHECK IF NOT self.object -> get object global ID from message

        splitted = message.split()
        # message    -> feeder_name - content
        # or message -> feeder_name

        # feeder_name - object
        if len(splitted) == 1:  # feeder_name - object   (content already saved)
            feeder_name = message
            gzip64encoded = ''

        # Feeder name in message: "feeder obj_id gzip64encoded"
        elif len(splitted) == 2:  # gzip64encoded content
            feeder_name, gzip64encoded = splitted
        else:
            self.logger.warning(f'Invalid Message: {splitted} not processed')
            return None

        if self.obj.type == 'item':
            # Remove ITEMS_FOLDER from item path (crawled item + submitted)
            # Limit basename length
            obj_id = self.obj.id
            self.obj.sanitize_id()
            if self.obj.id != obj_id:
                self.queue.rename_message_obj(self.obj.id, obj_id)


        # # TODO only work for item object
        # # Avoid any duplicate coming from any sources
        # if self.operation_mode == 1:
        #     digest = hashlib.sha1(gzip64encoded.encode('utf8')).hexdigest()
        #     if self.r_cache.exists(digest):  # Content already exists
        #         # STATS
        #         self.increase_stat_duplicate(feeder_name)
        #     else:  # New content
        #         self.r_cache.sadd(digest, feeder_name)
        #         self.r_cache.expire(digest, self.ttl_key)
        #
        #         self.increase_stat_processed(feeder_name)
        #         self.add_message_to_queue(message=relay_message)

        # Need To Be Fixed, Currently doesn't check the source (-> same as operation 1)
        # # Keep duplicate coming from different sources
        # elif self.operation_mode == 2:
        #     digest = hashlib.sha1(gzip64encoded.encode('utf8')).hexdigest()
        #     # Filter to avoid duplicate
        #     older_digest = self.r_cache.get(f'HASH_{item_id}')
        #     if older_digest is None:
        #         # New content
        #         # Store in redis for filtering
        #         self.r_cache.set(f'HASH_{item_id}', digest)
        #         self.r_cache.sadd(item_id, feeder_name)
        #         self.r_cache.expire(item_id, self.ttl_key)
        #         self.r_cache.expire(f'HASH_{item_id}', self.ttl_key)
        #
        #         self.add_message_to_queue(relay_message)
        #
        #     else:
        #         if digest != older_digest:
        #             # Same item name but different content
        #             # STATS
        #             self.increase_stat_duplicate(feeder_name)
        #             self.r_cache.sadd(item_id, feeder_name)
        #             self.r_cache.expire(item_id, ttl_key)
        #
        #             self.add_message_to_queue(relay_message)
        #
        #         else:
        #             # Already processed
        #             # Keep track of processed items
        #             # STATS
        #             self.increase_stat_duplicate(feeder_name)

        # No Filtering
        # else:

        self.increase_stat_processed(feeder_name)
        self.add_message_to_queue(obj=self.obj, message=gzip64encoded)


if __name__ == "__main__":
    module = Mixer()
    module.run()

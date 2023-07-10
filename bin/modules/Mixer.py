#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The Mixer Module
================

This module is consuming the Redis-list created by the ZMQ_Feed_Q Module.

This module take all the feeds provided in the config.


Depending on the configuration, this module will process the feed as follow:
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

import hashlib
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.ConfigLoader import ConfigLoader


class Mixer(AbstractModule):
    """docstring for Mixer module."""

    def __init__(self):
        super(Mixer, self).__init__()

        config_loader = ConfigLoader()
        self.r_cache = config_loader.get_redis_conn("Redis_Mixer_Cache")
        # self.r_cache_s = config_loader.get_redis_conn("Redis_Log_submit")

        self.pending_seconds = 5

        self.refresh_time = 30
        self.last_refresh = time.time()

        self.operation_mode = config_loader.get_config_int("Module_Mixer", "operation_mode")
        print(f'Operation mode {self.operation_mode}')

        self.ttl_key = config_loader.get_config_int("Module_Mixer", "ttl_duplicate")
        self.default_feeder_name = config_loader.get_config_str("Module_Mixer", "default_unnamed_feed_name")

        self.ITEMS_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'
        self.ITEMS_FOLDER = os.path.join(os.path.realpath(self.ITEMS_FOLDER), '')

        self.nb_processed_items = 0
        self.feeders_processed = {}
        self.feeders_duplicate = {}

        self.logger.info(f"Module: {self.module_name} Launched")

    # TODO Save stats in cache
    # def get_feeders(self):
    #     return self.r_cache_s.smembers("mixer_cache:feeders")
    #
    # def get_feeder_nb_last_processed(self, feeder):
    #     nb = self.r_cache_s.hget("mixer_cache:feeders:last_processed", feeder)
    #     if nb:
    #         return int(nb)
    #     else:
    #         return 0
    #
    # def get_cache_feeders_nb_last_processed(self):
    #     feeders = {}
    #     for feeder in self.get_feeders():
    #         feeders[feeder] = self.get_feeder_nb_last_processed(feeder)
    #     return feeders

    def clear_feeders_stat(self):
        pass
        # self.r_cache_s.delete("mixer_cache:feeders:last_processed")

    def increase_stat_processed(self, feeder):
        self.nb_processed_items += 1
        try:
            self.feeders_processed[feeder] += 1
        except KeyError:
            self.feeders_processed[feeder] = 1

    def increase_stat_duplicate(self, feeder):
        self.nb_processed_items += 1
        try:
            self.feeders_duplicate[feeder] += 1
        except KeyError:
            self.feeders_duplicate[feeder] = 1

    # TODO Save stats in cache
    def refresh_stats(self):
        if int(time.time() - self.last_refresh) > self.refresh_time:
            # update internal feeder
            to_print = f'Mixer; ; ; ;mixer_all All_feeders Processed {self.nb_processed_items} item(s) in {self.refresh_time}sec'
            print(to_print)
            self.redis_logger.info(to_print)
            self.nb_processed_items = 0

            for feeder in self.feeders_processed:
                to_print = f'Mixer; ; ; ;mixer_{feeder} {feeder} Processed {self.feeders_processed[feeder]} item(s) in {self.refresh_time}sec'
                print(to_print)
                self.redis_logger.info(to_print)
                self.feeders_processed[feeder] = 0

            for feeder in self.feeders_duplicate:
                to_print = f'Mixer; ; ; ;mixer_{feeder} {feeder} Duplicated {self.feeders_duplicate[feeder]} item(s) in {self.refresh_time}sec'
                print(to_print)
                self.redis_logger.info(to_print)
                self.feeders_duplicate[feeder] = 0

            self.last_refresh = time.time()
            self.clear_feeders_stat()
            time.sleep(0.5)

    def computeNone(self):
        self.refresh_stats()

    def compute(self, message):
        self.refresh_stats()
        splitted = message.split()
        # Old Feeder name "feeder>>item_id gzip64encoded"
        if len(splitted) == 2:
            item_id, gzip64encoded = splitted
            try:
                feeder_name, item_id = item_id.split('>>')
                feeder_name.replace(" ", "")
                if 'import_dir' in feeder_name:
                    feeder_name = feeder_name.split('/')[1]
            except ValueError:
                feeder_name = self.default_feeder_name
        # Feeder name in message: "feeder item_id gzip64encoded"
        elif len(splitted) == 3:
            feeder_name, item_id, gzip64encoded = splitted
        else:
            print('Invalid message: not processed')
            self.logger.debug(f'Invalid Item: {splitted[0]} not processed')
            return None

        # remove absolute path
        item_id = item_id.replace(self.ITEMS_FOLDER, '', 1)

        relay_message = f'{item_id} {gzip64encoded}'

        # Avoid any duplicate coming from any sources
        if self.operation_mode == 1:
            digest = hashlib.sha1(gzip64encoded.encode('utf8')).hexdigest()
            if self.r_cache.exists(digest):  # Content already exists
                # STATS
                self.increase_stat_duplicate(feeder_name)
            else:  # New content
                self.r_cache.sadd(digest, feeder_name)
                self.r_cache.expire(digest, self.ttl_key)

                self.increase_stat_processed(feeder_name)
                self.add_message_to_queue(relay_message)

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
        else:
            self.increase_stat_processed(feeder_name)
            self.add_message_to_queue(relay_message)


if __name__ == "__main__":
    module = Mixer()
    module.run()

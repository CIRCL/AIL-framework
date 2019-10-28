#!/usr/bin/python3

"""
The ``Domain``
===================


"""

import os
import sys
import time
import redis
import configparser

# Get Config file
config_dir = os.path.join(os.environ['AIL_HOME'], 'configs')
config_file = os.path.join(config_dir, 'core.cfg')
if not os.path.exists(config_file):
    raise Exception('Unable to find the configuration file. \
                    Did you set environment variables? \
                    Or activate the virtualenv.')

 # # TODO: create sphinx doc

 # # TODO: add config_field to reload

class ConfigLoader(object):
    """docstring for Config_Loader."""

    def __init__(self):
        self.cfg = configparser.ConfigParser()
        self.cfg.read(config_file)

    def get_redis_conn(self, redis_name, decode_responses=True): ## TODO: verify redis name
        return redis.StrictRedis( host=self.cfg.get(redis_name, "host"),
                                  port=self.cfg.getint(redis_name, "port"),
                                  db=self.cfg.getint(redis_name, "db"),
                                  decode_responses=decode_responses )

    def get_config_str(self, section, key_name):
        return self.cfg.get(section, key_name)

    def get_config_int(self, section, key_name):
        return self.cfg.getint(section, key_name)

    def get_config_boolean(self, section, key_name):
        return self.cfg.getboolean(section, key_name)

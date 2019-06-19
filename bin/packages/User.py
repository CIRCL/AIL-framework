#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import redis
import bcrypt
import configparser

from flask_login import UserMixin

class User(UserMixin):

    def __init__(self, id):

        configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
        if not os.path.exists(configfile):
            raise Exception('Unable to find the configuration file. \
                            Did you set environment variables? \
                            Or activate the virtualenv.')

        cfg = configparser.ConfigParser()
        cfg.read(configfile)

        self.r_serv_db = redis.StrictRedis(
            host=cfg.get("ARDB_DB", "host"),
            port=cfg.getint("ARDB_DB", "port"),
            db=cfg.getint("ARDB_DB", "db"),
            decode_responses=True)

        if self.r_serv_db.hexists('user:all', id):
            self.id = id
        else:
            self.id = "__anonymous__"

    # return True or False
    #def is_authenticated():

    # return True or False
    #def is_anonymous():

    @classmethod
    def get(self_class, id):
        return self_class(id)

    def check_password(self, password):
        password = password.encode()
        hashed_password = self.r_serv_db.hget('user:all', self.id).encode()
        if bcrypt.checkpw(password, hashed_password):
            return True
        else:
            return False

    def request_password_change(self):
        if self.r_serv_db.hget('user_metadata:{}'.format(self.id), 'change_passwd') == 'True':
            return True
        else:
            return False

    def is_in_role(self, role):
        if self.r_serv_db.sismember('user_role:{}'.format(role), self.id):
            return True
        else:
            return False

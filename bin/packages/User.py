#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis
import bcrypt

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

from flask_login import UserMixin

class User(UserMixin):

    def __init__(self, id):

        config_loader = ConfigLoader.ConfigLoader()

        self.r_serv_db = config_loader.get_redis_conn("ARDB_DB")
        config_loader = None

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

    def user_is_anonymous(self):
        if self.id == "__anonymous__":
            return True
        else:
            return False

    def check_password(self, password):
        if self.user_is_anonymous():
            return False

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

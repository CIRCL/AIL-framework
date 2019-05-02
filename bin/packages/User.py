#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import redis

from flask_login import UserMixin

class User(UserMixin):

    def __init__(self, id):
        self.id = 'abcdef'

    # return True or False
    #def is_authenticated():

    # return True or False
    #def is_active():

    # return True or False
    #def is_anonymous():

    @classmethod
    def get(self_class, id):
        print(id)
        return self_class(id)

    def check_password(self, password):
        print(self.id)
        if password=='admin':
            print('password ok')
            return True
        else:
            return False

    def set_password(self):
        return True

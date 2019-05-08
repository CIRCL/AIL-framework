#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis
import configparser

import bcrypt
import secrets

# Import config
sys.path.append('./modules/')

def hashing_password(bytes_password):
    hashed = bcrypt.hashpw(bytes_password, bcrypt.gensalt())
    return hashed

def create_user_db(username_id , password, default=False):
    password = password.encode()
    password_hash = hashing_password(password)
    r_serv_db.hset('user:all', username_id, password_hash)
    if default:
        r_serv_db.set('user:request_password_change', username_id)


if __name__ == "__main__":
    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    r_serv_db = redis.StrictRedis(
        host=cfg.get("ARDB_DB", "host"),
        port=cfg.getint("ARDB_DB", "port"),
        db=cfg.getint("ARDB_DB", "db"),
        decode_responses=True)

    username = 'admin@admin.test'
    # # TODO: create random password
    password = 'admin'
    create_user_db(username, password, default=True)

    # create user token
    token = secrets.token_urlsafe(41)
    r_serv_db.hset('user:tokens', token, username)

    print('new user created: {}'.format(username))
    print('password: {}'.format(password))

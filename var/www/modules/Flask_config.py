#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask global variables shared accross modules
'''
import configparser
import redis
import os

# FLASK #
app = None
#secret_key = 'ail-super-secret_key01C'

# CONFIG #
configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
if not os.path.exists(configfile):
    raise Exception('Unable to find the configuration file. \
                    Did you set environment variables? \
                    Or activate the virtualenv.')

cfg = configparser.ConfigParser()
cfg.read(configfile)


# REDIS #
r_serv = redis.StrictRedis(
    host=cfg.get("Redis_Queues", "host"),
    port=cfg.getint("Redis_Queues", "port"),
    db=cfg.getint("Redis_Queues", "db"),
    decode_responses=True)

r_serv_log = redis.StrictRedis(
    host=cfg.get("Redis_Log", "host"),
    port=cfg.getint("Redis_Log", "port"),
    db=cfg.getint("Redis_Log", "db"),
    decode_responses=True)

r_serv_log_submit = redis.StrictRedis(
    host=cfg.get("Redis_Log_submit", "host"),
    port=cfg.getint("Redis_Log_submit", "port"),
    db=cfg.getint("Redis_Log_submit", "db"),
    decode_responses=True)

r_serv_charts = redis.StrictRedis(
    host=cfg.get("ARDB_Trending", "host"),
    port=cfg.getint("ARDB_Trending", "port"),
    db=cfg.getint("ARDB_Trending", "db"),
    decode_responses=True)

r_serv_sentiment = redis.StrictRedis(
        host=cfg.get("ARDB_Sentiment", "host"),
        port=cfg.getint("ARDB_Sentiment", "port"),
        db=cfg.getint("ARDB_Sentiment", "db"),
        decode_responses=True)

r_serv_term = redis.StrictRedis(
        host=cfg.get("ARDB_TermFreq", "host"),
        port=cfg.getint("ARDB_TermFreq", "port"),
        db=cfg.getint("ARDB_TermFreq", "db"),
        decode_responses=True)

r_serv_cred = redis.StrictRedis(
        host=cfg.get("ARDB_TermCred", "host"),
        port=cfg.getint("ARDB_TermCred", "port"),
        db=cfg.getint("ARDB_TermCred", "db"),
        decode_responses=True)

r_serv_pasteName = redis.StrictRedis(
    host=cfg.get("Redis_Paste_Name", "host"),
    port=cfg.getint("Redis_Paste_Name", "port"),
    db=cfg.getint("Redis_Paste_Name", "db"),
    decode_responses=True)

r_serv_tags = redis.StrictRedis(
    host=cfg.get("ARDB_Tags", "host"),
    port=cfg.getint("ARDB_Tags", "port"),
    db=cfg.getint("ARDB_Tags", "db"),
    decode_responses=True)

r_serv_metadata = redis.StrictRedis(
    host=cfg.get("ARDB_Metadata", "host"),
    port=cfg.getint("ARDB_Metadata", "port"),
    db=cfg.getint("ARDB_Metadata", "db"),
    decode_responses=True)

# VARIABLES #
max_preview_char = int(cfg.get("Flask", "max_preview_char")) # Maximum number of character to display in the tooltip
max_preview_modal = int(cfg.get("Flask", "max_preview_modal")) # Maximum number of character to display in the modal

DiffMaxLineLength =  int(cfg.get("Flask", "DiffMaxLineLength"))#Use to display the estimated percentage instead of a raw value

bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

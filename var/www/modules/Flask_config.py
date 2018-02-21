#!/usr/bin/env python2
# -*-coding:UTF-8 -*

'''
    Flask global variables shared accross modules
'''
import ConfigParser
import redis
import os

# FLASK #
app = None

# CONFIG #
configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
if not os.path.exists(configfile):
    raise Exception('Unable to find the configuration file. \
                    Did you set environment variables? \
                    Or activate the virtualenv.')

cfg = ConfigParser.ConfigParser()
cfg.read(configfile)


# REDIS #
r_serv = redis.StrictRedis(
    host=cfg.get("Redis_Queues", "host"),
    port=cfg.getint("Redis_Queues", "port"),
    db=cfg.getint("Redis_Queues", "db"))

r_serv_log = redis.StrictRedis(
    host=cfg.get("Redis_Log", "host"),
    port=cfg.getint("Redis_Log", "port"),
    db=cfg.getint("Redis_Log", "db"))

r_serv_charts = redis.StrictRedis(
    host=cfg.get("Redis_Level_DB_Trending", "host"),
    port=cfg.getint("Redis_Level_DB_Trending", "port"),
    db=cfg.getint("Redis_Level_DB_Trending", "db"))

r_serv_sentiment = redis.StrictRedis(
        host=cfg.get("Redis_Level_DB_Sentiment", "host"),
        port=cfg.getint("Redis_Level_DB_Sentiment", "port"),
        db=cfg.getint("Redis_Level_DB_Sentiment", "db"))

r_serv_term = redis.StrictRedis(
        host=cfg.get("Redis_Level_DB_TermFreq", "host"),
        port=cfg.getint("Redis_Level_DB_TermFreq", "port"),
        db=cfg.getint("Redis_Level_DB_TermFreq", "db"))

r_serv_cred = redis.StrictRedis(
        host=cfg.get("Redis_Level_DB_TermCred", "host"),
        port=cfg.getint("Redis_Level_DB_TermCred", "port"),
        db=cfg.getint("Redis_Level_DB_TermCred", "db"))

r_serv_pasteName = redis.StrictRedis(
    host=cfg.get("Redis_Paste_Name", "host"),
    port=cfg.getint("Redis_Paste_Name", "port"),
    db=cfg.getint("Redis_Paste_Name", "db"))

# VARIABLES #
max_preview_char = int(cfg.get("Flask", "max_preview_char")) # Maximum number of character to display in the tooltip
max_preview_modal = int(cfg.get("Flask", "max_preview_modal")) # Maximum number of character to display in the modal

tlsh_to_percent = 1000.0 #Use to display the estimated percentage instead of a raw value
DiffMaxLineLength =  int(cfg.get("Flask", "DiffMaxLineLength"))#Use to display the estimated percentage instead of a raw value

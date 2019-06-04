#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask global variables shared accross modules
'''
import configparser
import redis
import os
import sys

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

r_cache = redis.StrictRedis(
    host=cfg.get("Redis_Cache", "host"),
    port=cfg.getint("Redis_Cache", "port"),
    db=cfg.getint("Redis_Cache", "db"),
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

r_serv_db = redis.StrictRedis(
    host=cfg.get("ARDB_DB", "host"),
    port=cfg.getint("ARDB_DB", "port"),
    db=cfg.getint("ARDB_DB", "db"),
    decode_responses=True)

r_serv_statistics = redis.StrictRedis(
    host=cfg.get("ARDB_Statistics", "host"),
    port=cfg.getint("ARDB_Statistics", "port"),
    db=cfg.getint("ARDB_Statistics", "db"),
    decode_responses=True)

r_serv_onion = redis.StrictRedis(
    host=cfg.get("ARDB_Onion", "host"),
    port=cfg.getint("ARDB_Onion", "port"),
    db=cfg.getint("ARDB_Onion", "db"),
    decode_responses=True)

sys.path.append('../../configs/keys')
# MISP #
try:
    from pymisp import PyMISP
    from mispKEYS import misp_url, misp_key, misp_verifycert
    pymisp = PyMISP(misp_url, misp_key, misp_verifycert)
    misp_event_url = misp_url + '/events/view/'
    print('Misp connected')
except:
    print('Misp not connected')
    pymisp = False
    misp_event_url = '#'
# The Hive #
try:
    from thehive4py.api import TheHiveApi
    import thehive4py.exceptions
    from theHiveKEYS import the_hive_url, the_hive_key, the_hive_verifycert
    if the_hive_url == '':
        HiveApi = False
        hive_case_url = '#'
        print('The HIVE not connected')
    else:
        HiveApi = TheHiveApi(the_hive_url, the_hive_key, cert=the_hive_verifycert)
        hive_case_url = the_hive_url+'/index.html#/case/id_here/details'
except:
    print('The HIVE not connected')
    HiveApi = False
    hive_case_url = '#'

if HiveApi != False:
    try:
        HiveApi.get_alert(0)
        print('The Hive connected')
    except thehive4py.exceptions.AlertException:
        HiveApi = False
        print('The Hive not connected')

# VARIABLES #
baseUrl = cfg.get("Flask", "baseurl")
baseUrl = baseUrl.replace('/', '')
if baseUrl != '':
    baseUrl = '/'+baseUrl

max_preview_char = int(cfg.get("Flask", "max_preview_char")) # Maximum number of character to display in the tooltip
max_preview_modal = int(cfg.get("Flask", "max_preview_modal")) # Maximum number of character to display in the modal

max_tags_result = 50

DiffMaxLineLength =  int(cfg.get("Flask", "DiffMaxLineLength"))#Use to display the estimated percentage instead of a raw value

bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

dict_update_description = {'v1.5':{'nb_background_update': 5, 'update_warning_message': 'An Update is running on the background. Some informations like Tags, screenshot can be',
                                   'update_warning_message_notice_me': 'missing from the UI.'}
                        }

UPLOAD_FOLDER = os.path.join(os.environ['AIL_FLASK'], 'submitted')

PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "pastes")) + '/'
SCREENSHOT_FOLDER = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "crawled_screenshot"), 'screenshot')

REPO_ORIGIN = 'https://github.com/CIRCL/AIL-framework.git'

max_dashboard_logs = int(cfg.get("Flask", "max_dashboard_logs"))

crawler_enabled = cfg.getboolean("Crawler", "activate_crawler")

# VT
try:
    from virusTotalKEYS import vt_key
    if vt_key != '':
        vt_auth = vt_key
        vt_enabled = True
        print('VT submission is enabled')
    else:
        vt_enabled = False
        print('VT submission is disabled')
except:
    vt_auth = {'apikey': cfg.get("Flask", "max_preview_char")}
    vt_enabled = False
    print('VT submission is disabled')

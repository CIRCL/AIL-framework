#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask global variables shared accross modules
'''
import os
import re
import sys

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

# FLASK #
app = None

# CONFIG #
config_loader = ConfigLoader.ConfigLoader()

# REDIS #
r_serv = config_loader.get_redis_conn("Redis_Queues")
r_cache = config_loader.get_redis_conn("Redis_Cache")
r_serv_log = config_loader.get_redis_conn("Redis_Log")
r_serv_log_submit = config_loader.get_redis_conn("Redis_Log_submit")
r_serv_charts = config_loader.get_redis_conn("ARDB_Trending")
r_serv_sentiment = config_loader.get_redis_conn("ARDB_Sentiment")
r_serv_term = config_loader.get_redis_conn("ARDB_Tracker")
r_serv_cred = config_loader.get_redis_conn("ARDB_TermCred")
r_serv_tags = config_loader.get_redis_conn("ARDB_Tags")
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
r_serv_db = config_loader.get_redis_conn("ARDB_DB")
r_serv_statistics = config_loader.get_redis_conn("ARDB_Statistics")
r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")

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

#### VARIABLES ####
baseUrl = config_loader.get_config_str("Flask", "baseurl")
baseUrl = baseUrl.replace('/', '')
if baseUrl != '':
    baseUrl = '/'+baseUrl

max_preview_char = int(config_loader.get_config_str("Flask", "max_preview_char")) # Maximum number of character to display in the tooltip
max_preview_modal = int(config_loader.get_config_str("Flask", "max_preview_modal")) # Maximum number of character to display in the modal

max_tags_result = 50

DiffMaxLineLength =  int(config_loader.get_config_str("Flask", "DiffMaxLineLength"))#Use to display the estimated percentage instead of a raw value

bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

dict_update_description = {'v1.5':{'nb_background_update': 5, 'update_warning_message': 'An Update is running on the background. Some informations like Tags, screenshot can be',
                                   'update_warning_message_notice_me': 'missing from the UI.'},
                           'v2.4':{'nb_background_update': 1, 'update_warning_message': 'An Update is running on the background. Some informations like Domain Tags/Correlation can be',
                                                              'update_warning_message_notice_me': 'missing from the UI.'},
                           'v2.6':{'nb_background_update': 1, 'update_warning_message': 'An Update is running on the background. Some informations like Domain Tags/Correlation can be',
                                                           'update_warning_message_notice_me': 'missing from the UI.'},
                           'v2.7':{'nb_background_update': 1, 'update_warning_message': 'An Update is running on the background. Some informations like Domain Tags can be',
                                                            'update_warning_message_notice_me': 'missing from the UI.'},
                           'v3.4':{'nb_background_update': 1, 'update_warning_message': 'An Update is running on the background. Some informations like Domain Languages can be',
                                                            'update_warning_message_notice_me': 'missing from the UI.'}
                        }

UPLOAD_FOLDER = os.path.join(os.environ['AIL_FLASK'], 'submitted')

PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'
SCREENSHOT_FOLDER = config_loader.get_files_directory('screenshot')

REPO_ORIGIN = 'https://github.com/ail-project/ail-framework.git'

max_dashboard_logs = int(config_loader.get_config_str("Flask", "max_dashboard_logs"))

crawler_enabled = config_loader.get_config_boolean("Crawler", "activate_crawler")

email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}'
email_regex = re.compile(email_regex)

IMPORT_MAX_TEXT_SIZE = 900000 # size in bytes

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
    vt_auth = {'apikey': config_loader.get_config_str("Flask", "max_preview_char")}
    vt_enabled = False
    print('VT submission is disabled')

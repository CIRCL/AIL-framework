#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.Items import Item
from lib.ail_core import get_ail_uuid
from lib.Investigations import Investigation
from lib.objects import ail_objects

## LOAD CONFIG ##
config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
r_db = config_loader.get_db_conn("Kvrocks_DB")

r_serv_db = config_loader.get_redis_conn("ARDB_DB")  ######################################
r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")  ######################################
config_loader = None
## -- ##

sys.path.append('../../configs/keys')
##################################
# Import Keys
##################################
from thehive4py.api import TheHiveApi
from thehive4py.models import Alert, AlertArtifact, Case, CaseObservable
import thehive4py.exceptions

from pymisp import MISPEvent, MISPObject, PyMISP

##################################
#           THE HIVE
##################################

HIVE_CLIENT = None
try:
    from theHiveKEYS import the_hive_url, the_hive_key, the_hive_verifycert

    HIVE_URL = the_hive_url
    HIVE_KEY = the_hive_key
    HIVE_VERIFY_CERT = the_hive_verifycert
except:
    HIVE_URL = None
    HIVE_KEY = None
    HIVE_VERIFY_CERT = None


def get_hive_client():
    global HIVE_CLIENT
    try:
        HIVE_CLIENT = TheHiveApi(HIVE_URL, HIVE_KEY, cert=HIVE_VERIFY_CERT)
    except:
        HIVE_CLIENT = None
    return HIVE_CLIENT


def is_hive_connected():
    try:
        # print(hive_client.health())
        HIVE_CLIENT.get_alert(0)
        return True
    except thehive4py.exceptions.AlertException:
        return False


HIVE_CLIENT = get_hive_client()

def sanitize_threat_level_hive(threat_level):
    try:
        int(threat_level)
        if 1 <= threat_level <= 3:
            return threat_level
        else:
            return 2
    except:
        return 2

def sanitize_tlp_hive(tlp):
    try:
        int(tlp)
        if 0 <= tlp <= 3:
            return tlp
        else:
            return 2
    except:
        return 2

def create_thehive_alert(item_id, tag_trigger):
    item = Item(item_id)
    meta = item.get_meta()
    # TheHive expects a file
    content = item.get_raw_content(decompress=True)

    # remove .gz from submitted path to TheHive because we've decompressed it
    if item_id.endswith(".gz"):
        item_id = item_id[:-3]
    # add .txt it's easier to open when downloaded from TheHive
    item_id = f'{item_id}.txt'

    artifacts = [
        AlertArtifact(dataType='other', message='uuid-ail', data=(get_ail_uuid())),
        AlertArtifact(dataType='file', data=(content, item_id), tags=meta['tags'])
    ]

    # Prepare the sample Alert
    sourceRef = str(uuid.uuid4())[0:6]
    alert = Alert(title='AIL Leak',
                  tlp=3,
                  tags=meta['tags'],
                  description='AIL Leak, triggered by {}'.format(tag_trigger),
                  type='ail',
                  source=meta['source'],  # Use item ID ?
                  sourceRef=sourceRef,
                  artifacts=artifacts)

    # Create the Alert
    alert_id = None
    try:
        response = HIVE_CLIENT.create_alert(alert)
        if response.status_code == 201:
            # print(json.dumps(response.json(), indent=4, sort_keys=True))
            print('Alert Created')
            print(response.json())
            alert_id = response.json()['id']
        else:
            print(f'ko: {response.status_code}/{response.text}')
            return 0
    except:
        print('hive connection error')
    print(alert_id)


# TODO SAVE CASE URL ????????????????????????
def create_thehive_case(item_id, title=None, tlp=2, threat_level=2, description=None):
    item = Item(item_id)
    ail_uuid = get_ail_uuid()

    if not title:
        title = f'AIL Case {item.id}'
    if not description:
        description = f'AIL {ail_uuid} Case'
    date = item.get_date()
    date = f'{date[0:4]}-{date[4:6]}-{date[6:8]}'
    tags = item.get_tags(r_list=True)

    case = Case(title=title,
                tlp=tlp,
                severity=threat_level,
                flag=False,
                tags=tags,
                description=description)

    # Create Case
    response = get_hive_client().create_case(case)
    if response.status_code == 201:
        case_id = response.json()['id']

        observables = [
            CaseObservable(dataType="other", data=[ail_uuid], message="uuid-ail"),
            CaseObservable(dataType="file", data=item.get_filename(), tags=tags),
            CaseObservable(dataType="other", data=[item.get_source()], message="source"),
            CaseObservable(dataType="other", data=[date], message="last-seen")
        ]

        for observable in observables:
            resp = HIVE_CLIENT.create_case_observable(case_id, observable)
            if resp.status_code != 201:
                print(f'error observable creation: {resp.status_code}/{resp.text}')
        # print(case_id)
        # return HIVE_URL /thehive/cases/~37040/details
        return case_id

        # r_serv_metadata.set('hive_cases:'+path, id)
    else:
        print(f'ko: {response.status_code}/{response.text}')
        return None


def get_case_url(case_id):
    return f'{HIVE_URL}/cases/{case_id}/details'


# TODO
def get_item_hive_cases(item_id):
    hive_case = r_serv_metadata.get('hive_cases:{}'.format(item_id))
    if hive_case:
        hive_case = the_hive_url + '/index.html#/case/{}/details'.format(hive_case)
    return hive_case


##################################
#           MISP
##################################

#####################################################################3

###########################################################
# # set default
# if r_serv_db.get('hive:auto-alerts') is None:
#     r_serv_db.set('hive:auto-alerts', 0)
#
# if r_serv_db.get('misp:auto-events') is None:
#     r_serv_db.set('misp:auto-events', 0)

# if __name__ == '__main__':
# from lib.objects.Cves import Cve
# create_misp_event([Item('crawled/2020/09/14/circl.lu0f4976a4-dda4-4189-ba11-6618c4a8c951'),
#                       Cve('CVE-2020-16856'), Cve('CVE-2014-6585'), Cve('CVE-2015-0383'),
#                       Cve('CVE-2015-0410')])

# create_investigation_misp_event('c6bbf8fa9ead4cc698eaeb07835cca5d)

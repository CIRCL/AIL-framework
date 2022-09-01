#!/usr/bin/env python3
# -*-coding:UTF-8 -*

##################################################################
##################################################################

# TODO:  /!\ MISP ORG UUID

##################################################################
##################################################################

import os
import sys
import datetime
import redis
import time
import uuid

from abc import ABC
from enum import Enum
from flask import escape

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
import Tag
from exceptions import UpdateInvestigationError

config_loader = ConfigLoader.ConfigLoader()
r_tracking = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None


#### UUID ####
def is_valid_uuid_v4(UUID):
    if not UUID:
        return False
    UUID = UUID.replace('-', '')
    try:
        uuid_test = uuid.UUID(hex=UUID, version=4)
        return uuid_test.hex == UUID
    except:
        return False

def sanityze_uuid(UUID):
    sanityzed_uuid = uuid.UUID(hex=UUID, version=4)
    return str(sanityzed_uuid).replace('-', '')

def exists_obj_type(obj_type):
    return obj_type in ['domain', 'item', 'pgp', 'cryptocurrency', 'decoded', 'screenshot', 'username']

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '')

##-- UUID --##

# status
# created
# last change
# tags
# comment/info
# level

## threat_level:
# 1 = high
# 2 = medium
# 3 = low
# 4 = undefined

## analysis:
# 0 = Initial
# 1 = Ongoing
# 2 = Complete

# # TODO: Save correlation between investigations ?

class ThreatLevel(Enum):
    high = 1
    medium = 2
    low = 3
    undefined = 4

class Analysis(Enum):
    initial = 0
    ongoing = 1
    completed = 2

class Investigation(object):
    """Investigation."""

    def __init__(self, investigation_uuid):
        self.uuid = investigation_uuid

    def get_uuid(self, separator=False):
        if separator:
            return uuid.UUID(hex=self.uuid, version=4)
        else:
            return self.uuid

    # # TODO: Replace by title ??????
    def get_name(self):
        return r_tracking.hget(f'investigations:data:{self.uuid}', 'name')

    def get_threat_level(self):
        try:
            return int(r_tracking.hget(f'investigations:data:{self.uuid}', 'threat_level'))
        except:
            return 1

    def get_threat_level_str(self):
        return ThreatLevel(self.get_threat_level()).name

    def get_analysis(self):
        try:
            return int(r_tracking.hget(f'investigations:data:{self.uuid}', 'analysis'))
        except:
            return 0

    def get_analysis_str(self):
        return Analysis(self.get_analysis()).name

    def get_tags(self):
        return r_tracking.smembers(f'investigations:tags:{self.uuid}')

    # save all editor ??????
    def get_creator_user(self):
        return r_tracking.hget(f'investigations:data:{self.uuid}', 'creator_user')

    def get_info(self):
        return r_tracking.hget(f'investigations:data:{self.uuid}', 'info')

    def get_date(self):
        return r_tracking.hget(f'investigations:data:{self.uuid}', 'date')

    def get_timestamp(self, r_str=False):
        timestamp = r_tracking.hget(f'investigations:data:{self.uuid}', 'timestamp')
        if r_str and timestamp:
            timestamp = datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        return timestamp

    def get_last_change(self, r_str=False):
        last_change = r_tracking.hget(f'investigations:data:{self.uuid}', 'last_change')
        if r_str and last_change:
            last_change = datetime.datetime.fromtimestamp(float(last_change)).strftime('%Y-%m-%d %H:%M:%S')
        return last_change

    def get_misp_events(self):
        return r_tracking.smembers(f'investigations:misp:{self.uuid}')

    # # TODO: DATE FORMAT
    def get_metadata(self, r_str=False):
        if r_str:
            analysis = self.get_analysis_str()
            threat_level = self.get_threat_level_str()
        else:
            analysis = self.get_analysis()
            threat_level = self.get_threat_level()
        return {'uuid': self.uuid,
                'name': self.get_name(),
                'threat_level': threat_level,
                'analysis': analysis,
                'tags': self.get_tags(),
                'user_creator': self.get_creator_user(),
                'date': self.get_date(),
                'timestamp': self.get_timestamp(r_str=r_str),
                'last_change': self.get_last_change(r_str=r_str),
                'info': self.get_info(),
                'nb_objects': self.get_nb_objects(),
                'misp_events': self.get_misp_events()}

    def set_name(self, name):
        r_tracking.hset(f'investigations:data:{self.uuid}', 'name', name)

    def set_info(self, info):
        r_tracking.hset(f'investigations:data:{self.uuid}', 'info', info)

    def set_date(self, date):
        r_tracking.hset(f'investigations:data:{self.uuid}', 'date', date)

    def set_last_change(self, last_change):
        r_tracking.hset(f'investigations:data:{self.uuid}', 'last_change', last_change)

    def set_threat_level(self, threat_level):
        try:
            threat_level = int(threat_level)
        except:
            raise UpdateInvestigationError('threat_level Not an integer')
        if threat_level >= 1 and threat_level <= 4:
            r_tracking.hset(f'investigations:data:{self.uuid}', 'threat_level', threat_level)
        else:
            raise UpdateInvestigationError(f'Invalid threat_level: {threat_level}')

    def set_analysis(self, analysis):
        try:
            analysis = int(analysis)
        except:
            raise UpdateInvestigationError('analysis Not an integer')
        if analysis >= 0 and analysis <= 2:
            r_tracking.hset(f'investigations:data:{self.uuid}', 'analysis', analysis)
        else:
            raise UpdateInvestigationError(f'Invalid analysis: {analysis}')

    def add_misp_events(self, misp_url):
        r_tracking.sadd(f'investigations:misp:{self.uuid}', misp_url)

    def set_tags(self, tags):
        # delete previous tags
        r_tracking.delete(f'investigations:tags:{self.uuid}')
        for tag in tags:
            r_tracking.sadd(f'investigations:tags:{self.uuid}', tag)

    def get_nb_objects(self):
        return r_tracking.scard(f'investigations:objs:{self.uuid}')

    def _get_objects(self):
        return r_tracking.smembers(f'investigations:objs:{self.uuid}')

    # # TODO: return Python object ???? ################################
    # TODO: PAGINATE
    def get_objects(self):
        # obj_dict = {}
        # for str_obj in self._get_objects():
        #     obj_type, subtype, id = str_obj.split(':', 2)
        #     if not obj_dict[obj_type]:
        #         obj_dict[obj_type] = []
        #     obj_dict[obj_type].append({'subtype': subtype, 'id': id})
        objs = []
        for str_obj in self._get_objects():
            obj_type, subtype, obj_id = str_obj.split(':', 2)
            dict_obj = {'type': obj_type, 'subtype': subtype, 'id': obj_id}
            objs.append(dict_obj)
        return objs

    # # TODO:  def register_object(self, Object): in OBJECT CLASS

    def register_object(self, obj_id, obj_type, subtype):
        r_tracking.sadd(f'investigations:objs:{self.uuid}', f'{obj_type}:{subtype}:{obj_id}')
        r_tracking.sadd(f'obj:investigations:{obj_type}:{subtype}:{obj_id}', self.uuid)
        timestamp = int(time.time())
        self.set_last_change(timestamp)


    def unregister_object(self, obj_id, obj_type, subtype):
        r_tracking.srem(f'investigations:objs:{self.uuid}', f'{obj_type}:{subtype}:{obj_id}')
        r_tracking.srem(f'obj:investigations:{obj_type}:{subtype}:{obj_id}', self.uuid)
        timestamp = int(time.time())
        self.set_last_change(timestamp)

    def delete(self):
        for str_obj in self._get_objects():
            obj_type, subtype, obj_id = str_obj.split(':', 2)
            self.unregister_object(obj_id, obj_type, subtype=subtype)

        r_tracking.srem('investigations:all', self.uuid)
        # user map
        r_tracking.srem(f'investigations:user:{self.get_creator_user()}', self.uuid)
        # metadata
        r_tracking.delete(f'investigations:data:{self.uuid}')
        r_tracking.delete(f'investigations:tags:{self.uuid}')
        r_tracking.delete(f'investigations:misp:{self.uuid}')

##--  Class  --##

def get_all_investigations():
    return r_tracking.smembers('investigations:all')

def exists_investigation(investigation_uuid):
    return r_tracking.sismember('investigations:all', investigation_uuid)

# created by user
def get_user_all_investigations(user_id):
    return r_tracking.smembers(f'investigations:user:{user_id}')

def is_object_investigated(obj_id, obj_type, subtype=''):
    return r_tracking.exists(f'obj:investigations:{obj_type}:{subtype}:{obj_id}')

def get_obj_investigations(obj_id, obj_type, subtype=''):
    return r_tracking.smembers(f'obj:investigations:{obj_type}:{subtype}:{obj_id}')

def delete_obj_investigations(obj_id, obj_type, subtype=''):
    unregistred = False
    for investigation_uuid in get_obj_investigations(obj_id, obj_type, subtype=subtype):
        investigation = Investigation(investigation_uuid)
        investigation.unregister_object(obj_id, obj_type, subtype)
        unregistred = True
    return unregistred


def _set_timestamp(investigation_uuid, timestamp):
    r_tracking.hset(f'investigations:data:{investigation_uuid}', 'timestamp', timestamp)

# analysis - threat level - info - date - creator

def _re_create_investagation(investigation_uuid, user_id, date, name, threat_level, analysis, info, tags, last_change, timestamp, misp_events):
    create_investigation(user_id, date, name, threat_level, analysis, info, tags=tags, investigation_uuid=investigation_uuid)
    if timestamp:
        _set_timestamp(investigation_uuid, timestamp)
    investigation = Investigation(investigation_uuid)
    if last_change:
        investigation.set_last_change(last_change)
    for misp_event in misp_events:
        investigation.add_misp_events(misp_event)

# # TODO: fix default threat_level analysis
# # TODO: limit description + name
# # TODO: sanityze tags
# # TODO: sanityze date
def create_investigation(user_id, date, name, threat_level, analysis, info, tags=[], investigation_uuid=None):
    if investigation_uuid:
        if not is_valid_uuid_v4(investigation_uuid):
            investigation_uuid = generate_uuid()
    else:
        investigation_uuid = generate_uuid()
    r_tracking.sadd('investigations:all', investigation_uuid)
    # user map
    r_tracking.sadd(f'investigations:user:{user_id}', investigation_uuid)
    # metadata
    r_tracking.hset(f'investigations:data:{investigation_uuid}', 'creator_user', user_id)

    # TODO: limit info + name
    investigation = Investigation(investigation_uuid)
    investigation.set_info(info)
    #investigation.set_name(name) ##############################################
    investigation.set_date(date)
    investigation.set_threat_level(threat_level)
    investigation.set_analysis(analysis)

    # # TODO: sanityze tags
    if tags:
        investigation.set_tags(tags)

    timestamp = int(time.time())
    r_tracking.hset(f'investigations:data:{investigation_uuid}', 'timestamp', timestamp)
    investigation.set_last_change(timestamp)

    return investigation_uuid

def get_all_investigations_meta(r_str=False):
    investigations_meta = []
    for investigation_uuid in get_all_investigations():
        investigation = Investigation(investigation_uuid)
        investigations_meta.append(investigation.get_metadata(r_str=r_str))
    return investigations_meta

def get_investigations_selector():
    l_investigations = []
    for investigation_uuid in get_all_investigations():
        investigation = Investigation(investigation_uuid)
        name = investigation.get_info()
        l_investigations.append({"id":investigation_uuid, "name": name})
    return l_investigations

    #{id:'8dc4b81aeff94a9799bd70ba556fa345',name:"Paris"}


####  API  ####

# # TODO: CHECK Mandatory Fields
# # TODO: SANITYZE Fields
# # TODO: Name ?????
def api_add_investigation(json_dict):
    user_id = json_dict.get('user_id')
    name = json_dict.get('name') ##### mandatory ?
    name = escape(name)
    threat_level = json_dict.get('threat_level', 4)
    analysis = json_dict.get('analysis', 0)

    # # TODO: sanityze date
    date = json_dict.get('date')

    info = json_dict.get('info', '')
    info = escape(info)
    info = info[:1000]
    tags = json_dict.get('tags', [])
    if not Tag.are_enabled_tags(tags):
        return {"status": "error", "reason": "Invalid/Disabled tags"}, 400

    try:
        res = create_investigation(user_id, date, name, threat_level, analysis, info, tags=tags)
    except UpdateInvestigationError as e:
        return e.message, 400
    return res, 200

# # TODO: edit threat level / status
def api_edit_investigation(json_dict):
    investigation_uuid = json_dict.get('uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(investigation_uuid):
        return {"status": "error", "reason": "Invalid Investigation uuid"}, 400
    investigation_uuid = sanityze_uuid(investigation_uuid)
    if not exists_investigation(investigation_uuid):
        return {"status": "error", "reason": "Investigation not found"}, 404
    investigation = Investigation(investigation_uuid)

    name = json_dict.get('name') ##### mandatory ?
    name = escape(name)
    threat_level = json_dict.get('threat_level', 4)
    try:
        investigation.set_threat_level(threat_level)
    except UpdateInvestigationError:
        return {"status": "error", "reason": "Invalid Investigation threat_level"}, 400

    analysis = json_dict.get('analysis', 0)
    try:
        investigation.set_analysis(analysis)
    except UpdateInvestigationError:
        return {"status": "error", "reason": "Invalid Investigation analysis"}, 400

    info = json_dict.get('info', '')
    info = escape(info)
    info = info[:1000]
    tags = json_dict.get('tags', [])
    if not Tag.are_enabled_tags(tags):
        return {"status": "error", "reason": "Invalid/Disabled tags"}, 400

    investigation.set_info(info)
    investigation.set_name(name)
    investigation.set_tags(tags)

    timestamp = int(time.time())
    investigation.set_last_change(timestamp)

    return investigation_uuid, 200

def api_delete_investigation(json_dict):
    investigation_uuid = json_dict.get('uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(investigation_uuid):
        return {"status": "error", "reason": "Invalid Investigation uuid"}, 400
    investigation_uuid = sanityze_uuid(investigation_uuid)
    if not exists_investigation(investigation_uuid):
        return {"status": "error", "reason": "Investigation not found"}, 404
    investigation = Investigation(investigation_uuid)
    res = investigation.delete()
    return res, 200

def api_register_object(json_dict):
    investigation_uuid = json_dict.get('uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(investigation_uuid):
        return {"status": "error", "reason": f"Invalid Investigation uuid: {investigation_uuid}"}, 400
    investigation_uuid = sanityze_uuid(investigation_uuid)
    if not exists_investigation(investigation_uuid):
        return {"status": "error", "reason": f"Investigation not found: {investigation_uuid}"}, 404
    investigation = Investigation(investigation_uuid)

    obj_type = json_dict.get('type', '').replace(' ', '')
    if not exists_obj_type(obj_type):
        return {"status": "error", "reason": f"Invalid Object Type: {obj_type}"}, 400

    subtype = json_dict.get('subtype', '')
    if subtype == 'None':
        subtype = ''
    obj_id = json_dict.get('id', '').replace(' ', '')
    res = investigation.register_object(obj_id, obj_type, subtype)
    return res, 200

def api_unregister_object(json_dict):
    investigation_uuid = json_dict.get('uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(investigation_uuid):
        return {"status": "error", "reason": f"Invalid Investigation uuid: {investigation_uuid}"}, 400
    investigation_uuid = sanityze_uuid(investigation_uuid)
    if not exists_investigation(investigation_uuid):
        return {"status": "error", "reason": f"Investigation not found: {investigation_uuid}"}, 404
    investigation = Investigation(investigation_uuid)

    obj_type = json_dict.get('type', '').replace(' ', '')
    subtype = json_dict.get('subtype', '')
    if subtype == 'None':
        subtype = ''
    obj_id = json_dict.get('id', '').replace(' ', '')
    res = investigation.unregister_object(obj_id, obj_type, subtype)
    return res, 200

##--  API  --##


if __name__ == '__main__':
    # res = create_star_list(user_id, name, description)
    # print(res)

    # res = r_tracking.dbsize()
    # print(res)

    investigation_uuid = 'a6545c38083444eeb9383d357f8fa747'
    _set_timestamp(investigation_uuid, int(time.time()))

    # investigation = Investigation(investigation_uuid)
    # investigation.delete()

# # TODO: PAGINATION

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
import time
import uuid

from enum import Enum
from markupsafe import escape

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_core
from lib import ail_orgs
from lib import ConfigLoader
from lib import Tag
from lib.exceptions import UpdateInvestigationError

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

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '')

## -- UUID -- ##

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

    def _get_field(self, field):
        return r_tracking.hget(f'investigations:data:{self.uuid}', field)

    def _set_field(self, field, value):
        r_tracking.hset(f'investigations:data:{self.uuid}', field, value)

    def exists(self):
        return r_tracking.exists(f'investigations:data:{self.uuid}')

    def get_uuid(self, separator=False):
        if separator:
            return uuid.UUID(hex=self.uuid, version=4)
        else:
            return self.uuid

    # # TODO: Replace by title ??????
    def get_name(self):
        return r_tracking.hget(f'investigations:data:{self.uuid}', 'name')

    ## LEVEL ##

    def get_level(self):
        return int(r_tracking.hget(f'investigations:data:{self.uuid}', 'level'))

    def set_level(self, level, org_uuid):
        r_tracking.hset(f'investigations:data:{self.uuid}', 'level', level)
        # Global
        if level == 1:
            r_tracking.sadd('investigations', self.uuid)
        # Org
        elif level == 2:
            self.add_to_org(org_uuid)

    def reset_level(self, old_level, new_level, new_org_uuid):
        if old_level == 1:
            r_tracking.srem('investigations', self.uuid)
        # Org
        elif old_level == 2:
            ail_orgs.remove_obj_to_org(self.get_org(), 'investigation', self.uuid)
        self.set_level(new_level, new_org_uuid)

    def check_level(self, user_org):
        level = self.get_level()
        if level == 1:
            return True
        elif level == 2:
            return self.get_org() == user_org

    ## ORG ##

    def get_creator_org(self):
        return r_tracking.hget(f'investigations:data:{self.uuid}', 'creator_org')

    def get_org(self):
        return r_tracking.hget(f'investigations:data:{self.uuid}', 'org')

    def add_to_org(self, org_uuid):
        r_tracking.hset(f'investigations:data:{self.uuid}', 'org', org_uuid)
        ail_orgs.add_obj_to_org(org_uuid, 'investigation', self.uuid)

    ## -ORG- ##

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

    # def get_misp_events(self):
    #     return r_tracking.smembers(f'investigations:misp:{self.uuid}')

    # # TODO: DATE FORMAT
    def get_metadata(self, options=set(), r_str=False):
        if r_str:
            analysis = self.get_analysis_str()
            threat_level = self.get_threat_level_str()
        else:
            analysis = self.get_analysis()
            threat_level = self.get_threat_level()

        # 'name': self.get_name(),
        meta = {'uuid': self.uuid,
                'threat_level': threat_level,
                'analysis': analysis,
                'tags': list(self.get_tags()),
                'user_creator': self.get_creator_user(),
                'level': self.get_level(),
                'org': self.get_org(),
                'date': self.get_date(),
                'timestamp': self.get_timestamp(r_str=r_str),
                'last_change': self.get_last_change(r_str=r_str),
                'info': self.get_info(),
                'nb_objects': self.get_nb_objects(),
                # 'misp_events': list(self.get_misp_events())
                }
        if 'objects' in options:
            meta['objects'] = self.get_objects()
        if 'org_name' in options and meta['org']:
            meta['org_name'] = ail_orgs.Organisation(self.get_org()).get_name()
        return meta

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
        except TypeError:
            raise UpdateInvestigationError('threat_level Not an integer')
        if 1 <= threat_level <= 4:
            r_tracking.hset(f'investigations:data:{self.uuid}', 'threat_level', threat_level)
        else:
            raise UpdateInvestigationError(f'Invalid threat_level: {threat_level}')

    def set_analysis(self, analysis):
        try:
            analysis = int(analysis)
        except TypeError:
            raise UpdateInvestigationError('analysis Not an integer')
        if 0 <= analysis <= 2:
            r_tracking.hset(f'investigations:data:{self.uuid}', 'analysis', analysis)
        else:
            raise UpdateInvestigationError(f'Invalid analysis: {analysis}')

    def add_misp_events(self, event_uuid):
        r_tracking.sadd(f'investigations:misp:{self.uuid}', event_uuid)

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

    def get_objects_comment(self, obj_global_id):
        return r_tracking.hget(f'investigations:objs:comment:{self.uuid}', obj_global_id)

    def set_objects_comment(self, obj_global_id, comment):
        if comment:
            r_tracking.hset(f'investigations:objs:comment:{self.uuid}', obj_global_id, comment)

    # # TODO:  def register_object(self, Object): in OBJECT CLASS

    def register_object(self, obj_id, obj_type, subtype, comment=''):
        r_tracking.sadd(f'investigations:objs:{self.uuid}', f'{obj_type}:{subtype}:{obj_id}')
        r_tracking.sadd(f'obj:investigations:{obj_type}:{subtype}:{obj_id}', self.uuid)
        if comment:
            self.set_objects_comment(f'{obj_type}:{subtype}:{obj_id}', comment)
        timestamp = int(time.time())
        self.set_last_change(timestamp)

    def unregister_object(self, obj_id, obj_type, subtype):
        r_tracking.srem(f'investigations:objs:{self.uuid}', f'{obj_type}:{subtype}:{obj_id}')
        r_tracking.srem(f'obj:investigations:{obj_type}:{subtype}:{obj_id}', self.uuid)
        r_tracking.hdel(f'investigations:objs:comment:{self.uuid}', f'{obj_type}:{subtype}:{obj_id}')
        timestamp = int(time.time())
        self.set_last_change(timestamp)

    def delete(self):
        for str_obj in self._get_objects():
            obj_type, subtype, obj_id = str_obj.split(':', 2)
            self.unregister_object(obj_id, obj_type, subtype=subtype)

        r_tracking.srem('investigations:all', self.uuid)
        # level
        level = self.get_level()
        if level == 1:
            r_tracking.srem('investigations', self.uuid)
        elif level == 2:
            ail_orgs.remove_obj_to_org(self.get_org(), 'investigation', self.uuid)

        # user map
        r_tracking.srem(f'investigations:user:{self.get_creator_user()}', self.uuid)
        # metadata
        r_tracking.delete(f'investigations:data:{self.uuid}')
        r_tracking.delete(f'investigations:tags:{self.uuid}')
        r_tracking.delete(f'investigations:misp:{self.uuid}')
        return self.uuid

## --  -- ##

def get_all_investigations():
    return r_tracking.smembers('investigations:all')

def exists_investigation(investigation_uuid):
    return r_tracking.sismember('investigations:all', investigation_uuid)

def get_global_investigations():
    return r_tracking.smembers('investigations')

def get_org_investigations(org_uuid):
    return ail_orgs.get_org_objs_by_type(org_uuid, 'investigation')

# created by user
def get_user_all_investigations(user_id):
    return r_tracking.smembers(f'investigations:user:{user_id}')

def is_object_investigated(obj_id, obj_type, subtype=''):
    return r_tracking.exists(f'obj:investigations:{obj_type}:{subtype}:{obj_id}')

def get_obj_investigations(obj_id, obj_type, subtype=''):
    return r_tracking.smembers(f'obj:investigations:{obj_type}:{subtype}:{obj_id}')

def delete_obj_investigations(obj_id, obj_type, subtype=''):
    unregistered = False
    for investigation_uuid in get_obj_investigations(obj_id, obj_type, subtype=subtype):
        investigation = Investigation(investigation_uuid)
        investigation.unregister_object(obj_id, obj_type, subtype)
        unregistered = True
    return unregistered


def _set_timestamp(investigation_uuid, timestamp):
    r_tracking.hset(f'investigations:data:{investigation_uuid}', 'timestamp', timestamp)

# analysis - threat level - info - date - creator

def _re_create_investigation(investigation_uuid, user_org, user_id, level, date, name, threat_level, analysis, info, tags, last_change, timestamp, misp_events):
    create_investigation(user_org, user_id, level, date, name, threat_level, analysis, info, tags=tags, investigation_uuid=investigation_uuid)
    if timestamp:
        _set_timestamp(investigation_uuid, timestamp)
    investigation = Investigation(investigation_uuid)
    if last_change:
        investigation.set_last_change(last_change)
    for misp_event in misp_events:
        investigation.add_misp_events(misp_event)

# # TODO: fix default threat_level analysis
# # TODO: limit description + name
# # TODO: sanitize tags
# # TODO: sanitize date
def create_investigation(user_org, user_id, level, date, name, threat_level, analysis, info, tags=[], investigation_uuid=None):
    if investigation_uuid:
        if not is_valid_uuid_v4(investigation_uuid):
            investigation_uuid = generate_uuid()
    else:
        investigation_uuid = generate_uuid()
    r_tracking.sadd('investigations:all', investigation_uuid)
    # user map
    r_tracking.sadd(f'investigations:user:{user_id}', investigation_uuid)    # TODO REFACTOR ME
    # metadata
    r_tracking.hset(f'investigations:data:{investigation_uuid}', 'creator_org', user_org)
    r_tracking.hset(f'investigations:data:{investigation_uuid}', 'creator_user', user_id)

    # TODO: limit info + name
    investigation = Investigation(investigation_uuid)
    investigation.set_level(level, user_org)

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

def get_global_investigations_meta(r_str=False):
    investigations_meta = []
    for investigation_uuid in get_global_investigations():
        investigation = Investigation(investigation_uuid)
        investigations_meta.append(investigation.get_metadata(r_str=r_str))
    return investigations_meta


def get_org_investigations_meta(org_uuid, r_str=False):
    investigations_meta = []
    for investigation_uuid in get_org_investigations(org_uuid):
        investigation = Investigation(investigation_uuid)
        investigations_meta.append(investigation.get_metadata(r_str=r_str, options={'org_name'}))
    return investigations_meta

def get_orgs_investigations_meta(r_str=False):
    investigations_meta = []
    for tracker_uuid in get_all_investigations():
        inv = Investigation(tracker_uuid)
        if inv.get_level() == 2:
            investigations_meta.append(inv.get_metadata(r_str=r_str, options={'org_name'}))
    return investigations_meta


def get_investigations_selector(org_uuid):
    l_investigations = []
    for investigation_uuid in get_global_investigations():
        investigation = Investigation(investigation_uuid)
        name = investigation.get_info()
        l_investigations.append({"id": investigation_uuid, "name": name})
    for investigation_uuid in get_org_investigations(org_uuid):
        investigation = Investigation(investigation_uuid)
        name = investigation.get_info()
        l_investigations.append({"id": investigation_uuid, "name": name})
    return l_investigations

####  ACL  ####

def api_check_investigation_acl(inv, user_org, user_id, user_role, action):
    if not ail_orgs.check_obj_access_acl(inv, user_org, user_id, user_role, action):
        return {"status": "error", "reason": "Access Denied"}, 403

def api_is_allowed_to_edit_investigation_level(inv, user_org, user_id, user_role, new_level):
    if not ail_orgs.check_acl_edit_level(inv, user_org, user_id, user_role, new_level):
        return {"status": "error", "reason": "Access Denied - Investigation level"}, 403

####  API  ####

def api_get_investigation(user_org, user_id, user_role, investigation_uuid):  # TODO check if is UUIDv4
    investigation = Investigation(investigation_uuid)
    if not investigation.exists():
        return {'status': 'error', 'reason': 'Investigation Not Found'}, 404
    res = api_check_investigation_acl(investigation, user_org, user_id, user_role, 'view')
    if res:
        return res

    meta = investigation.get_metadata(options={'objects'}, r_str=False)
    # objs = []
    # for obj in investigation.get_objects():
    #     obj_meta = ail_objects.get_object_meta(obj["type"], obj["subtype"], obj["id"], flask_context=True)
    #     comment = investigation.get_objects_comment(f'{obj["type"]}:{obj["subtype"]}:{obj["id"]}')
    #     if comment:
    #         obj_meta['comment'] = comment
    #     objs.append(obj_meta)
    return meta, 200

# # TODO: CHECK Mandatory Fields
# # TODO: SANITYZE Fields
# # TODO: Name ?????
def api_add_investigation(json_dict):
    user_org = json_dict.get('user_org')
    user_id = json_dict.get('user_id')
    name = json_dict.get('name') ##### mandatory ?
    name = escape(name)
    threat_level = json_dict.get('threat_level', 4)
    analysis = json_dict.get('analysis', 0)

    # # TODO: sanityze date
    date = json_dict.get('date')

    level = json_dict.get('level', 1)
    try:
        level = int(level)
    except TypeError:
        level = 1
    if level not in range(1, 3):
        level = 1

    info = json_dict.get('info', '')
    info = escape(info)
    info = info[:1000]
    tags = json_dict.get('tags', [])
    if not Tag.are_enabled_tags(tags):
        return {"status": "error", "reason": "Invalid/Disabled tags"}, 400

    try:
        res = create_investigation(user_org, user_id, level, date, name, threat_level, analysis, info, tags=tags)
    except UpdateInvestigationError as e:
        return e.message, 400
    return res, 200

# # TODO: edit threat level / status
def api_edit_investigation(user_org, user_id, user_role, json_dict):
    investigation_uuid = json_dict.get('uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(investigation_uuid):
        return {"status": "error", "reason": "Invalid Investigation uuid"}, 400
    investigation_uuid = sanityze_uuid(investigation_uuid)
    if not exists_investigation(investigation_uuid):
        return {"status": "error", "reason": "Investigation not found"}, 404
    investigation = Investigation(investigation_uuid)
    res = api_check_investigation_acl(investigation, user_org, user_id, user_role, 'edit')
    if res:
        return res

    level = json_dict.get('level', 1)
    try:
        level = int(level)
    except TypeError:
        level = 1
    if level not in range(1, 3):
        level = 1
    res = api_is_allowed_to_edit_investigation_level(investigation, user_org, user_id, user_role, level)
    if res:
        return res

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

    old_level = investigation.get_level()
    if level != old_level:
        investigation.reset_level(old_level, level, user_org)

    investigation.set_info(info)
    investigation.set_name(name)
    investigation.set_tags(tags)

    timestamp = int(time.time())
    investigation.set_last_change(timestamp)

    return investigation_uuid, 200

def api_delete_investigation(user_org, user_id, user_role, json_dict):
    investigation_uuid = json_dict.get('uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(investigation_uuid):
        return {"status": "error", "reason": "Invalid Investigation uuid"}, 400
    investigation_uuid = sanityze_uuid(investigation_uuid)
    if not exists_investigation(investigation_uuid):
        return {"status": "error", "reason": "Investigation not found"}, 404
    investigation = Investigation(investigation_uuid)
    res = api_check_investigation_acl(investigation, user_org, user_id, user_role, 'delete')
    if res:
        return res
    res = investigation.delete()
    return res, 200

def api_register_object(user_org, user_id, user_role, json_dict):
    investigation_uuid = json_dict.get('uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(investigation_uuid):
        return {"status": "error", "reason": f"Invalid Investigation uuid: {investigation_uuid}"}, 400
    investigation_uuid = sanityze_uuid(investigation_uuid)
    if not exists_investigation(investigation_uuid):
        return {"status": "error", "reason": f"Investigation not found: {investigation_uuid}"}, 404
    investigation = Investigation(investigation_uuid)
    res = api_check_investigation_acl(investigation, user_org, user_id, user_role, 'edit')
    if res:
        return res

    obj_type = json_dict.get('type', '').replace(' ', '')
    if obj_type not in ail_core.get_all_objects():
        return {"status": "error", "reason": f"Invalid Object Type: {obj_type}"}, 400

    subtype = json_dict.get('subtype', '')
    if subtype == 'None':
        subtype = ''
    obj_id = json_dict.get('id', '').rstrip()

    comment = json_dict.get('comment', '')
    # if comment:
    #     comment = escape(comment)
    res = investigation.register_object(obj_id, obj_type, subtype, comment=comment)
    return res, 200

def api_unregister_object(user_org, user_id, user_role, json_dict):
    investigation_uuid = json_dict.get('uuid', '').replace(' ', '')
    if not is_valid_uuid_v4(investigation_uuid):
        return {"status": "error", "reason": f"Invalid Investigation uuid: {investigation_uuid}"}, 400
    investigation_uuid = sanityze_uuid(investigation_uuid)
    if not exists_investigation(investigation_uuid):
        return {"status": "error", "reason": f"Investigation not found: {investigation_uuid}"}, 404
    investigation = Investigation(investigation_uuid)
    res = api_check_investigation_acl(investigation, user_org, user_id, user_role, 'edit')
    if res:
        return res

    obj_type = json_dict.get('type', '').replace(' ', '')
    subtype = json_dict.get('subtype', '')
    if subtype == 'None':
        subtype = ''
    obj_id = json_dict.get('id', '').replace(' ', '')
    res = investigation.unregister_object(obj_id, obj_type, subtype)
    return res, 200

## -- API -- ##

#
# if __name__ == '__main__':
#     # res = create_star_list(user_id, name, description)
#     # print(res)
#
#     # res = r_tracking.dbsize()
#     # print(res)
#
#     investigation_uuid = 'a6545c38083444eeb9383d357f8fa747'
#     _set_timestamp(investigation_uuid, int(time.time()))
#
#     # investigation = Investigation(investigation_uuid)
#     # investigation.delete()

# # TODO: PAGINATION

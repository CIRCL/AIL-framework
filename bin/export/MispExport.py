#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import io
import sys
import uuid

sys.path.append(os.environ['AIL_BIN'])
from lib.objects import ail_objects

from export import AILObjects


from lib.Investigations import Investigation

# # TODO: # FIXME: REFACTOR ME => use UI/Global config
sys.path.append('../../configs/keys')
try:
    from mispKEYS import misp_url, misp_key, misp_verifycert
except:
    misp_url = ''
    misp_key = ''
    misp_verifycert = False

# MISP
from pymisp import MISPEvent, MISPObject, PyMISP

def is_valid_obj_to_export(obj_type, obj_subtype, obj_id):
    if not ail_objects.is_valid_object_type(obj_type):
        return False
    if not ail_objects.is_valid_object_subtype(obj_type, obj_subtype):
        return False
    if not ail_objects.exists_obj(obj_type, obj_subtype, obj_id):
        return False
    return True

def sanitize_obj_export_lvl(lvl):
    try:
        lvl = int(lvl)
    except:
        lvl = 0
    return lvl

def get_export_filename(json_content):
    return 'ail_export_{}.json'.format(json_content.uuid)

def create_in_memory_file(json_content):
    return io.BytesIO(json_content.encode())

def add_relation_ship_to_create(set_relationship, dict_obj, dict_new_obj):
    global_id = ail_objects.get_obj_global_id(dict_obj['type'], dict_obj.get('subtype', ''), dict_obj['id'])
    global_id_new = ail_objects.get_obj_global_id(dict_new_obj['type'], dict_new_obj.get('subtype', ''), dict_new_obj['id'])
    if global_id > global_id_new:
        res = (global_id, global_id_new)
    else:
        res = (global_id_new, global_id)
    set_relationship.add( res )

# # TODO: add action by obj type
# ex => Domain
def add_obj_to_create(all_obj_to_export, set_relationship, dict_obj):
    all_obj_to_export.add(ail_objects.get_obj_global_id(dict_obj['type'], dict_obj.get('subtype', ''), dict_obj['id']))

def add_obj_to_create_by_lvl(all_obj_to_export, set_relationship, dict_obj, lvl):
    # # TODO: filter by export mode or filter on all global ?
    if lvl >= 0:
        add_obj_to_create(all_obj_to_export, add_obj_to_create, dict_obj)

    if lvl > 0:
        lvl = lvl - 1

        # # TODO: filter by correlation types
        obj_correlations = ail_objects.get_obj_correlations(dict_obj['type'], dict_obj.get('subtype', ''), dict_obj['id'])
        for obj_type in obj_correlations:
            dict_new_obj = {'type': obj_type}
            if obj_type=='pgp' or obj_type=='cryptocurrency' or obj_type=='username':
                for subtype in obj_correlations[obj_type]:
                    dict_new_obj['subtype'] = subtype
                    for obj_id in obj_correlations[obj_type][subtype]:
                        dict_new_obj['id'] = obj_id
                        add_obj_to_create_by_lvl(all_obj_to_export, set_relationship, dict_new_obj, lvl)
                        add_relation_ship_to_create(set_relationship, dict_obj, dict_new_obj)

            else:
                for obj_id in obj_correlations[obj_type]:
                    dict_new_obj['id'] = obj_id
                    add_obj_to_create_by_lvl(all_obj_to_export, set_relationship, dict_new_obj, lvl)
                    add_relation_ship_to_create(set_relationship, dict_obj, dict_new_obj)


        add_obj_to_create_by_lvl(all_obj_to_export, set_relationship, dict_obj, lvl)


def create_list_of_objs_to_export(l_obj, r_type='json'):
    all_obj_to_export = set()
    set_relationship = set()
    for obj in l_obj:
        add_obj_to_create_by_lvl(all_obj_to_export, set_relationship, obj, obj.get('lvl', 1))

    # create MISP objects
    dict_misp_obj = create_all_misp_obj(all_obj_to_export, set_relationship)

    # create object relationships
    for obj_global_id_1, obj_global_id_2 in set_relationship:
        dict_relationship = get_relationship_between_global_obj(obj_global_id_1, obj_global_id_2)
        if dict_relationship:
            obj_src = dict_misp_obj[dict_relationship['src']]
            obj_dest = dict_misp_obj[dict_relationship['dest']]
            obj_src.add_reference(obj_dest.uuid, dict_relationship['relation'], 'add a comment')

    event = MISPEvent()
    event.info = 'AIL framework export'
    event.uuid = str(uuid.uuid4())
    for obj_global_id in dict_misp_obj:
        misp_obj = dict_misp_obj[obj_global_id]
        AILObjects.create_map_obj_event_uuid(event.uuid, obj_global_id)
        AILObjects.create_map_obj_uuid_golbal_id(event.uuid, obj_global_id)
        if misp_obj:
            # add object to event
            event.add_object(dict_misp_obj[obj_global_id])

    return event

# TODO REFACTOR ME
def create_all_misp_obj(all_obj_to_export, set_relationship):
    dict_misp_obj = {}
    for obj_global_id in all_obj_to_export:
        obj_type, obj_id = obj_global_id.split(':', 1)
        dict_misp_obj[obj_global_id] = create_misp_obj(obj_type, obj_id)
    return dict_misp_obj

# TODO REFACTOR ME
def create_misp_obj(obj_type, obj_id):
    if obj_type in ['cryptocurrency', 'pgp', 'username']:
        obj_subtype, obj_id = obj_id.split(':', 1)
    else:
        obj_subtype = ''
    misp_obj = ail_objects.get_misp_object(obj_type, obj_subtype, obj_id)
    return misp_obj


def get_relationship_between_global_obj(obj_global_id_1, obj_global_id_2):
    obj_type_1 = obj_global_id_1.split(':', 1)[0]
    obj_type_2 = obj_global_id_2.split(':', 1)[0]
    type_tuple = [obj_type_1, obj_type_2]

    if 'image' in type_tuple: # or screenshot ## TODO:
        if obj_type_1 == 'image':
            src = obj_global_id_1
            dest = obj_global_id_2
        else:
            src = obj_global_id_2
            dest = obj_global_id_1
        return {'relation': 'screenshot-of', 'src': src, 'dest': dest}
    elif 'decoded' in type_tuple:
        if obj_type_1 == 'decoded':
            src = obj_global_id_1
            dest = obj_global_id_2
        else:
            src = obj_global_id_2
            dest = obj_global_id_1
        return {'relation': 'included-in', 'src': src, 'dest': dest}
    elif 'pgp' in type_tuple:
        if obj_type_1 == 'pgp':
            src = obj_global_id_1
            dest = obj_global_id_2
        else:
            src = obj_global_id_2
            dest = obj_global_id_1
        return {'relation': 'extracted-from', 'src': src, 'dest': dest}
    elif 'cryptocurrency':
        if obj_type_1 == 'cryptocurrency':
            src = obj_global_id_1
            dest = obj_global_id_2
        else:
            src = obj_global_id_2
            dest = obj_global_id_1
        return {'relation': 'extracted-from', 'src': src, 'dest': dest}
    elif 'domain' in type_tuple:
        if 'item' in type_tuple:
            if obj_type_1 == 'item':
                src = obj_global_id_1
                dest = obj_global_id_2
            else:
                src = obj_global_id_2
                dest = obj_global_id_1
            return {'relation': 'extracted-from', 'src': src, 'dest': dest} # replave by crawled-from
    elif 'item' in type_tuple:
        if 'domain' in type_tuple:
            if obj_type_1 == 'item':
                src = obj_global_id_1
                dest = obj_global_id_2
            else:
                src = obj_global_id_2
                dest = obj_global_id_1
            return {'relation': 'extracted-from', 'src': src, 'dest': dest} # replave by crawled-from
    return None

def sanitize_event_distribution(distribution):
    try:
        int(distribution)
        if (0 <= distribution <= 3):
            return distribution
        else:
            return 0
    except:
        return 0

def sanitize_event_threat_level_id(threat_level_id):
    try:
        int(threat_level_id)
        if (1 <= threat_level_id <= 4):
            return threat_level_id
        else:
            return 4
    except:
        return 4

def sanitize_event_analysis(analysis):
    try:
        int(analysis)
        if (0 <= analysis <= 2):
            return analysis
        else:
            return 0
    except:
        return 0

# # TODO: return error
def ping_misp():
    try:
        PyMISP(misp_url, misp_key, misp_verifycert)
        return True
    except Exception as e:
        print(e)
        return False

def create_misp_event(event, distribution=0, threat_level_id=4, publish=False, analysis=0, event_info=None):
    if event_info:
        event.info = event_info
    event.distribution = sanitize_event_distribution(distribution)
    event.threat_level_id = sanitize_event_threat_level_id(threat_level_id)
    event.analysis = sanitize_event_analysis(analysis)
    if publish:
        event.publish()

    # # TODO: handle multiple MISP instance
    misp = PyMISP(misp_url, misp_key, misp_verifycert)
    #print(event.to_json())

    misp_event = misp.add_event(event)
     #print(misp_event)
    # # TODO: handle error
    event_metadata = extract_event_metadata(misp_event)
    return event_metadata

def extract_event_metadata(event):
    event_metadata = {}
    event_metadata['uuid'] = event['Event']['uuid']
    event_metadata['id'] = event['Event']['id']
    if misp_url[-1] == '/':
        event_metadata['url'] = misp_url + 'events/view/' + str(event_metadata['id'])
    else:
        event_metadata['url'] = misp_url + '/events/view/' + str(event_metadata['id'])
    return event_metadata

######
#
# EXPORT LVL DEFINITION: (== Correl<tion DEPTH)
#
# LVL 0 => PARTIAL    Only add core item Correlation
# LVL 1 => DETAILED   Also add correlated_items correlation
######

# # TODO: # create object relationships
def create_investigation_event(investigation_uuid):
    investigation = Investigation(investigation_uuid)

    event = MISPEvent()
    event.info = investigation.get_info()
    event.uuid = investigation.get_uuid(separator=True)
    event.date = investigation.get_date()
    event.analysis = investigation.get_analysis()
    event.threat_level_id = investigation.get_threat_level()

    event.distribution = 0

    # tags
    for tag in investigation.get_tags():
        event.add_tag(tag)
    # objects
    investigation_objs = investigation.get_objects()
    for obj in investigation_objs:
        # if subtype -> obj_id = 'subtype:type'
        if obj['subtype']:
            obj_id = f"{obj['subtype']}:{obj['id']}"
        else:
            obj_id = obj['id']
        misp_obj = create_misp_obj(obj['type'], obj_id)
        if misp_obj:
            event.add_object(misp_obj)

    # if publish:
    #     event.publish()

    # print(event.to_json())
    misp = PyMISP(misp_url, misp_key, misp_verifycert)
    if misp.event_exists(event.uuid):
        misp_event = misp.update_event(event)
    else:
        misp_event = misp.add_event(event)

    # # TODO: handle error
    event_metadata = extract_event_metadata(misp_event)
    if event_metadata.get('uuid'):
        if misp_url[-1] == '/':
            url =  misp_url[:-1]
        else:
            url =  misp_url
        investigation.add_misp_events(url)
    return event_metadata

# if __name__ == '__main__':

    # l_obj = [{'id': 'bfd5f1d89e55b10a8b122a9d7ce31667ec1d086a', 'type': 'decoded', 'lvl': 2}]
    # create_list_of_objs_to_export(l_obj)

    #print(event.to_json())

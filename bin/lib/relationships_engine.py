#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_rel = config_loader.get_db_conn("Kvrocks_Relationships")
config_loader = None


RELATIONSHIPS = {
    "forward",  # forwarded_to
    "mention"
}

RELATIONSHIPS_OBJS = {
    "forward": {
        'chat': {'chat', 'message'},
        'message': {'chat'}
    },
    "mention": {}
}

def get_relationships():
    return RELATIONSHIPS

def sanitize_relationships(relationships):
    rels = get_relationships()
    if relationships:
        relationships = set(relationships).intersection(rels)
    if not relationships:
        relationships = rels
        if not relationships:
            return []
    return relationships

def get_relationship_obj_types(relationship):
    return RELATIONSHIPS_OBJS.get(relationship, {})

def get_relationship_objs(relationship, obj_type):
    return get_relationship_obj_types(relationship).get(obj_type, set())

def sanityze_obj_types(relationship, obj_type, filter_types):
    objs_types = get_relationship_objs(relationship, obj_type)
    if filter_types:
        filter_types = objs_types.intersection(filter_types)
    if not filter_types:
        filter_types = objs_types
        if not filter_types:
            return []
    return filter_types

# TODO check obj_type
# TODO sanitize relationships

def get_obj_relationships_by_type(obj_global_id, relationship, filter_types=set()):
    obj_type = obj_global_id.split(':', 1)[0]
    relationships = {}
    filter_types = sanityze_obj_types(relationship, obj_type, filter_types)
    for o_type in filter_types:
        relationships[o_type] = r_rel.smembers(f'rel:{relationship}:{obj_global_id}:{o_type}')
    return relationships

def get_obj_nb_relationships_by_type(obj_global_id, relationship, filter_types=set()):
    obj_type = obj_global_id.split(':', 1)[0]
    relationships = {}
    filter_types = sanityze_obj_types(relationship, obj_type, filter_types)
    for o_type in filter_types:
        relationships[o_type] = r_rel.scard(f'rel:{relationship}:{obj_global_id}:{o_type}')
    return relationships

def get_obj_relationships(obj_global_id, relationships=set(), filter_types=set()):
    all_relationships = []
    for relationship in relationships:
        obj_relationships = get_obj_relationships_by_type(obj_global_id, relationship, filter_types=filter_types)
        for obj_type in obj_relationships:
            for rel in obj_relationships[obj_type]:
                meta = {'relationship': relationship}
                direction, obj_id = rel.split(':', 1)
                if direction == 'i':
                    meta['source'] = obj_id
                    meta['target'] = obj_global_id
                else:
                    meta['target'] = obj_id
                    meta['source'] = obj_global_id

                meta['id'] = obj_id
                # meta['direction'] = direction
                all_relationships.append(meta)
    return all_relationships

def get_obj_nb_relationships(obj_global_id): # TODO###########################################################################################
    nb = {}
    for relationship in get_relationships():
        nb[relationship] = get_obj_nb_relationships_by_type(obj_global_id, relationship)
    return nb


# TODO Filter by obj type ???
def add_obj_relationship(source, target, relationship):
    source_type = source.split(':', 1)[0]
    target_type = target.split(':', 1)[0]
    r_rel.sadd(f'rel:{relationship}:{source}:{target_type}', f'o:{target}')
    r_rel.sadd(f'rel:{relationship}:{target}:{source_type}', f'i:{source}')


def get_relationship_graph(obj_global_id, relationships=[], filter_types=[], max_nodes=300, level=1, objs_hidden=set()):
    links = []
    nodes = set()
    meta = {'complete': True, 'objs': set()}
    done = set()
    done_link = set()

    _get_relationship_graph(obj_global_id, links, nodes, meta, level, max_nodes, relationships=relationships, filter_types=filter_types, objs_hidden=objs_hidden, done=done, done_link=done_link)
    return nodes, links, meta

def _get_relationship_graph(obj_global_id, links, nodes, meta, level, max_nodes, relationships=[], filter_types=[], objs_hidden=set(), done=set(), done_link=set()):
    meta['objs'].add(obj_global_id)
    nodes.add(obj_global_id)

    for rel in get_obj_relationships(obj_global_id, relationships=relationships, filter_types=filter_types):
        meta['objs'].add(rel['id'])

        if rel['id'] in done:
            continue

        if len(nodes) > max_nodes != 0:
            meta['complete'] = False
            break

        nodes.add(rel['id'])

        str_link = f"{rel['source']}{rel['target']}{rel['relationship']}"
        if str_link not in done_link:
            links.append({"source": rel['source'], "target": rel['target'], "relationship": rel['relationship']})
            done_link.add(str_link)

        if level > 0:
            next_level = level - 1

            _get_relationship_graph(rel['id'], links, nodes, meta, next_level, max_nodes, relationships=relationships, filter_types=filter_types, objs_hidden=objs_hidden, done=done, done_link=done_link)

    # done.add(rel['id'])


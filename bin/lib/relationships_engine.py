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
    "forward",
    "mention"
}
def get_relationships():
    return RELATIONSHIPS


def get_obj_relationships_by_type(obj_global_id, relationship):
    return r_rel.smembers(f'rel:{relationship}:{obj_global_id}')

def get_obj_nb_relationships_by_type(obj_global_id, relationship):
    return r_rel.scard(f'rel:{relationship}:{obj_global_id}')

def get_obj_relationships(obj_global_id):
    relationships = []
    for relationship in get_relationships():
        for rel in get_obj_relationships_by_type(obj_global_id, relationship):
            meta = {'relationship': relationship}
            direction, obj_id = rel.split(':', 1)
            if direction == 'i':
                meta['source'] = obj_id
                meta['target'] = obj_global_id
            else:
                meta['target'] = obj_id
                meta['source'] = obj_global_id

            if not obj_id.startswith('chat'):
                continue

            meta['id'] = obj_id
            # meta['direction'] = direction
            relationships.append(meta)
    return relationships

def get_obj_nb_relationships(obj_global_id):
    nb = {}
    for relationship in get_relationships():
        nb[relationship] = get_obj_nb_relationships_by_type(obj_global_id, relationship)
    return nb


# TODO Filter by obj type ???
def add_obj_relationship(source, target, relationship):
    r_rel.sadd(f'rel:{relationship}:{source}', f'o:{target}')
    r_rel.sadd(f'rel:{relationship}:{target}', f'i:{source}')
    # r_rel.sadd(f'rels:{source}', relationship)
    # r_rel.sadd(f'rels:{target}', relationship)


def get_relationship_graph(obj_global_id, filter_types=[], max_nodes=300, level=1, objs_hidden=set()):
    links = []
    nodes = set()
    meta = {'complete': True, 'objs': set()}
    done = set()
    done_link = set()

    _get_relationship_graph(obj_global_id, links, nodes, meta, level, max_nodes, filter_types=filter_types, objs_hidden=objs_hidden, done=done, done_link=done_link)
    return nodes, links, meta

def _get_relationship_graph(obj_global_id, links, nodes, meta, level, max_nodes, filter_types=[], objs_hidden=set(), done=set(), done_link=set()):
    meta['objs'].add(obj_global_id)
    nodes.add(obj_global_id)

    for rel in get_obj_relationships(obj_global_id):
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

            _get_relationship_graph(rel['id'], links, nodes, meta, next_level, max_nodes, filter_types=filter_types, objs_hidden=objs_hidden, done=done, done_link=done_link)

    # done.add(rel['id'])


if __name__ == '__main__':
    source = ''
    target = ''
    add_obj_relationship(source, target, 'forward')
    # print(get_obj_relationships(source))

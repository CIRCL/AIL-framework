# -*-coding:UTF-8 -*
"""
GEO engine helpers for AIL objects.
"""

import os
import sys

sys.path.append(os.environ['AIL_BIN'])

from lib.ConfigLoader import ConfigLoader
from lib import ail_core

config_loader = ConfigLoader()
r_geo = config_loader.get_db_conn("Kvrocks_GEO")
config_loader = None


def create_geo_id():
    """Create a compact GEO identifier."""
    return ail_core.generate_uuid().replace("-", "")


def add_geo_to_object(obj_gid, obj_type, lon, lat, probability=None, geo_id=None):
    """Create a GEO observation point for an object and index it."""
    if not geo_id:
        geo_id = create_geo_id()

    geo_key = f'g:{geo_id}'
    r_geo.hset(geo_key, 'o', obj_gid)
    if probability is not None:
        r_geo.hset(geo_key, 'p', probability)

    obj_geo_key = f'o:{obj_gid}'
    obj_type_geo_key = f'objs:{obj_type}'
    r_geo.geoadd(obj_geo_key, [lon, lat, geo_id])
    r_geo.geoadd(obj_type_geo_key, [lon, lat, geo_id])
    return geo_id


def remove_geo_from_object(obj_gid, obj_type, geo_id):
    """Remove one GEO observation point from all indexes and metadata."""
    removed_object = r_geo.zrem(f'o:{obj_gid}', geo_id)
    removed_obj_type = r_geo.zrem(f'objs:{obj_type}', geo_id)
    removed_meta = r_geo.delete(f'g:{geo_id}')
    return bool(removed_object or removed_obj_type or removed_meta)


def object_has_geo(obj_gid):
    """Return whether an object has at least one GEO observation point."""
    return r_geo.zcard(f'o:{obj_gid}') > 0


def delete_all_geo_from_object(obj_gid, obj_type):
    """Delete all GEO observation points attached to an object."""
    obj_key = f'o:{obj_gid}'
    type_key = f'objs:{obj_type}'
    geo_ids = r_geo.zrange(obj_key, 0, -1)
    if not geo_ids:
        return 0

    r_geo.zrem(type_key, *geo_ids)
    meta_keys = [f'g:{geo_id}' for geo_id in geo_ids]
    r_geo.delete(*meta_keys)
    r_geo.delete(obj_key)
    return len(geo_ids)


def get_geo_probability(geo_id):
    """Return the stored GEO probability if present."""
    return r_geo.hget(f'g:{geo_id}', 'p')


def get_geo_object_gid(geo_id):
    """Return the object global id attached to one GEO id."""
    return r_geo.hget(f'g:{geo_id}', 'o')


def get_geo_position(obj_gid, geo_id):
    """Return one GEO position from the canonical object GEO key."""
    return r_geo.geopos(f'o:{obj_gid}', geo_id)


def get_all_geo_positions(obj_gid):
    """Return all GEO positions for one object."""
    obj_key = f'o:{obj_gid}'
    geo_ids = r_geo.zrange(obj_key, 0, -1)
    if not geo_ids:
        return []

    positions = r_geo.geopos(obj_key, *geo_ids)
    geos = []
    for geo_id, pos in zip(geo_ids, positions):
        geos.append({'geo_id': geo_id, 'position': pos})
    return geos


def get_object_nb_geos(obj_gid):
    """Return the number of GEO points attached to one object."""
    return r_geo.zcard(f'o:{obj_gid}')


def yield_objects_type_geos(obj_type):
    """Yield all GEO observations for one object type."""
    type_key = f'objs:{obj_type}'
    geo_ids = r_geo.zrange(type_key, 0, -1)
    if not geo_ids:
        return

    positions = r_geo.geopos(type_key, *geo_ids)
    for geo_id, pos in zip(geo_ids, positions):
        yield {
            'geo_id': geo_id,
            'obj_gid': r_geo.hget(f'g:{geo_id}', 'o'),
            'position': pos,
            'probability': r_geo.hget(f'g:{geo_id}', 'p')
        }

# -*-coding:UTF-8 -*
"""Geolocation records and spatial indexes in the dedicated Kvrocks GEO database."""

import configparser
import math
import re
import time
import uuid

from redis.exceptions import WatchError


GEO_MAX_LATITUDE = 85.05112878
MAX_PAGE_SIZE = 1000
TRANSACTION_RETRIES = 8
r_geo = None


class GeoConflictError(ValueError):
    """The location belongs to another object, already exists, or changed concurrently."""


class GeoOwnershipError(GeoConflictError):
    """The requested location is not owned by the supplied object."""


class GeoStorageError(RuntimeError):
    """A GEO record or index has an unexpected storage format."""


class GeoConfigurationError(RuntimeError):
    """The dedicated geolocation database connection is not configured correctly."""


def _get_geo_db():
    global r_geo
    if r_geo is None:
        from lib.ConfigLoader import ConfigLoader
        try:
            r_geo = ConfigLoader().get_db_conn('Kvrocks_GEO')
        except (configparser.Error, ValueError) as err:
            raise GeoConfigurationError('Geolocation database configuration is missing or invalid. Run python bin/Update-conf.py and check [Kvrocks_GEO] in configs/core.cfg.') from err
    return r_geo


def _validate_owner(obj_gid, obj_type=None):
    if not isinstance(obj_gid, str):
        raise ValueError('Object global ID must be a string')
    parts = obj_gid.split(':', 2)
    if len(parts) != 3 or not re.fullmatch(r'[a-z][a-z0-9-]*', parts[0]) or not parts[2]:
        raise ValueError('Object global ID must use type:subtype:id')
    if any(ord(character) < 32 for character in obj_gid):
        raise ValueError('Object global ID must not contain control characters')
    if obj_type is not None and obj_type != parts[0]:
        raise ValueError('Object type does not match its global ID')
    return parts[0]


def _validate_geo_id(geo_id):
    if not isinstance(geo_id, str):
        raise ValueError('Geolocation ID must be a UUID4')
    try:
        parsed = uuid.UUID(geo_id)
    except ValueError as err:
        raise ValueError('Geolocation ID must be a UUID4') from err
    if parsed.version != 4:
        raise ValueError('Geolocation ID must be a UUID4')
    return parsed.hex


def _validate_coordinate(value, name, maximum):
    if isinstance(value, bool):
        raise ValueError(f'{name} must be a finite number')
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as err:
        raise ValueError(f'{name} must be a finite number') from err
    if not math.isfinite(value) or not -maximum <= value <= maximum:
        raise ValueError(f'{name} must be between {-maximum} and {maximum}')
    return value


def _validate_coordinates(lon, lat):
    return _validate_coordinate(lon, 'Longitude', 180), _validate_coordinate(lat, 'Latitude', 90)


def _validate_provenance(value, name):
    if value is not None and (not isinstance(value, str) or not value or len(value) > 512 or any(ord(character) < 32 for character in value)):
        raise ValueError(f'{name} must be a nonempty string without control characters, at most 512 characters')
    return value


def _validate_revision(expected_revision):
    if expected_revision is not None and (isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 1):
        raise ValueError('Expected revision must be a positive integer')


def get_indexed_latitude(latitude):
    """Keep original WGS84 coordinates in records and clamp only the index latitude."""
    latitude = _validate_coordinate(latitude, 'Latitude', 90)
    return max(-GEO_MAX_LATITUDE, min(GEO_MAX_LATITUDE, latitude))


def create_geo_id():
    return uuid.uuid4().hex


def _check_key_types(pipe, key_types):
    for key, expected_type in key_types.items():
        if pipe.type(key) not in {'none', expected_type}:
            raise GeoStorageError(f'Unexpected key type for {key}; expected {expected_type}')


def _run_transaction(key_types, operation):
    db = _get_geo_db()
    for _ in range(TRANSACTION_RETRIES):
        with db.pipeline(transaction=True) as pipe:
            try:
                pipe.watch(*key_types)
                _check_key_types(pipe, key_types)
                result = operation(pipe)
                pipe.execute()
                return result
            except WatchError:
                continue
    raise GeoConflictError('Geolocation changed concurrently; retry the operation')


def _decode_geo(geo_id, record, obj_gid=None):
    if not record:
        return None
    if obj_gid is not None and record.get('obj_gid') != obj_gid:
        raise GeoOwnershipError('Geolocation belongs to another object')
    try:
        _validate_owner(record['obj_gid'])
        longitude, latitude = _validate_coordinates(record['longitude'], record['latitude'])
        created_at, updated_at, revision = int(record['created_at']), int(record['updated_at']), int(record['revision'])
        if created_at < 0 or updated_at < created_at or revision < 1:
            raise ValueError('Invalid timestamps or revision')
        geo = {'geo_id': geo_id, 'obj_gid': record['obj_gid'], 'longitude': longitude, 'latitude': latitude,
               'created_at': created_at, 'updated_at': updated_at, 'revision': revision}
        for field in ('created_by', 'updated_by', 'source'):
            if field in record:
                geo[field] = _validate_provenance(record[field], field)
        return geo
    except (KeyError, ValueError, TypeError) as err:
        raise GeoStorageError(f'Invalid geolocation record {geo_id}') from err


def add_geo_to_object(obj_gid, obj_type, lon, lat, geo_id=None, created_by=None, source=None):
    """Create one location; an explicit ID is reserved for trusted importers."""
    obj_type = _validate_owner(obj_gid, obj_type)
    lon, lat = _validate_coordinates(lon, lat)
    _validate_provenance(created_by, 'Creator')
    _validate_provenance(source, 'Source')
    geo_id = _validate_geo_id(geo_id) if geo_id is not None else create_geo_id()
    key_types = {f'geo:observation:{geo_id}': 'hash', f'geo:object:{obj_gid}': 'zset',
                 'geo:index:all': 'zset', f'geo:index:type:{obj_type}': 'zset'}

    def create(pipe):
        if pipe.exists(f'geo:observation:{geo_id}'):
            raise GeoConflictError('Geolocation ID already exists')
        timestamp = time.time_ns() // 1_000_000
        record = {'obj_gid': obj_gid, 'longitude': lon, 'latitude': lat, 'created_at': timestamp, 'updated_at': timestamp, 'revision': 1}
        if created_by is not None:
            record.update(created_by=created_by, updated_by=created_by)
        if source is not None:
            record['source'] = source
        pipe.multi()
        pipe.hset(f'geo:observation:{geo_id}', mapping=record)
        pipe.zadd(f'geo:object:{obj_gid}', {geo_id: timestamp})
        pipe.geoadd('geo:index:all', [lon, get_indexed_latitude(lat), geo_id])
        pipe.geoadd(f'geo:index:type:{obj_type}', [lon, get_indexed_latitude(lat), geo_id])
        return geo_id

    return _run_transaction(key_types, create)


def get_geo_from_object(obj_gid, geo_id):
    """Read original coordinates, checking the immutable owner."""
    _validate_owner(obj_gid)
    geo_id = _validate_geo_id(geo_id)
    return _decode_geo(geo_id, _get_geo_db().hgetall(f'geo:observation:{geo_id}'), obj_gid)


def get_object_geos(obj_gid, offset=0, limit=100):
    """List locations in creation order; pagination applies to location entries."""
    _validate_owner(obj_gid)
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError('Offset must be a nonnegative integer')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_PAGE_SIZE:
        raise ValueError(f'Limit must be between 1 and {MAX_PAGE_SIZE}')
    db = _get_geo_db()
    geo_ids = db.zrange(f'geo:object:{obj_gid}', offset, offset + limit - 1)
    if not geo_ids:
        return []
    with db.pipeline(transaction=False) as pipe:
        for geo_id in geo_ids:
            pipe.hgetall(f'geo:observation:{geo_id}')
        records = pipe.execute()
    geos = []
    for geo_id, record in zip(geo_ids, records):
        geo = _decode_geo(geo_id, record, obj_gid)
        if geo is not None:
            geos.append(geo)
    return geos


def update_geo_from_object(obj_gid, obj_type, geo_id, lon, lat, expected_revision=None, updated_by=None):
    """Update a location without changing its ID, owner, or creation order."""
    obj_type = _validate_owner(obj_gid, obj_type)
    geo_id = _validate_geo_id(geo_id)
    lon, lat = _validate_coordinates(lon, lat)
    _validate_revision(expected_revision)
    _validate_provenance(updated_by, 'Editor')
    key_types = {f'geo:observation:{geo_id}': 'hash', f'geo:object:{obj_gid}': 'zset',
                 'geo:index:all': 'zset', f'geo:index:type:{obj_type}': 'zset'}

    def update(pipe):
        geo = _decode_geo(geo_id, pipe.hgetall(f'geo:observation:{geo_id}'), obj_gid)
        if geo is None:
            pipe.multi()
            return None
        if expected_revision is not None and expected_revision != geo['revision']:
            raise GeoConflictError('Geolocation revision changed')
        if pipe.zscore(f'geo:object:{obj_gid}', geo_id) is None:
            raise GeoStorageError('Geolocation is missing from its object membership')
        if lon == geo['longitude'] and lat == geo['latitude']:
            pipe.multi()
            return geo
        geo.update(longitude=lon, latitude=lat, updated_at=max(geo['updated_at'], time.time_ns() // 1_000_000), revision=geo['revision'] + 1)
        fields = {field: geo[field] for field in ('longitude', 'latitude', 'updated_at', 'revision')}
        if updated_by is not None:
            geo['updated_by'] = updated_by
            fields['updated_by'] = updated_by
        pipe.multi()
        pipe.hset(f'geo:observation:{geo_id}', mapping=fields)
        pipe.geoadd('geo:index:all', [lon, get_indexed_latitude(lat), geo_id])
        pipe.geoadd(f'geo:index:type:{obj_type}', [lon, get_indexed_latitude(lat), geo_id])
        return geo

    return _run_transaction(key_types, update)


def remove_geo_from_object(obj_gid, obj_type, geo_id, expected_revision=None):
    """Remove one location atomically; a missing location is an idempotent no-op."""
    obj_type = _validate_owner(obj_gid, obj_type)
    geo_id = _validate_geo_id(geo_id)
    _validate_revision(expected_revision)
    key_types = {f'geo:observation:{geo_id}': 'hash', f'geo:object:{obj_gid}': 'zset',
                 'geo:index:all': 'zset', f'geo:index:type:{obj_type}': 'zset'}

    def remove(pipe):
        record = pipe.hgetall(f'geo:observation:{geo_id}')
        owner = record.get('obj_gid')
        if owner is not None and owner != obj_gid:
            raise GeoOwnershipError('Geolocation belongs to another object')
        if record and expected_revision is not None and _decode_geo(geo_id, record, obj_gid)['revision'] != expected_revision:
            raise GeoConflictError('Geolocation revision changed')
        if owner is None and pipe.zscore(f'geo:object:{obj_gid}', geo_id) is None:
            pipe.multi()
            return False
        pipe.multi()
        pipe.zrem(f'geo:object:{obj_gid}', geo_id)
        pipe.zrem('geo:index:all', geo_id)
        pipe.zrem(f'geo:index:type:{obj_type}', geo_id)
        pipe.delete(f'geo:observation:{geo_id}')
        return True

    return _run_transaction(key_types, remove)


def delete_all_geo_from_object(obj_gid, obj_type):
    """Guard the membership snapshot so concurrent additions cannot become orphans."""
    obj_type = _validate_owner(obj_gid, obj_type)
    key_types = {f'geo:object:{obj_gid}': 'zset', 'geo:index:all': 'zset', f'geo:index:type:{obj_type}': 'zset'}

    def remove_all(pipe):
        geo_ids = pipe.zrange(f'geo:object:{obj_gid}', 0, -1)
        if not geo_ids:
            pipe.multi()
            return 0
        record_keys = {f'geo:observation:{geo_id}': 'hash' for geo_id in geo_ids}
        pipe.watch(*record_keys)
        _check_key_types(pipe, record_keys)
        for geo_id in geo_ids:
            owner = pipe.hget(f'geo:observation:{geo_id}', 'obj_gid')
            if owner is not None and owner != obj_gid:
                raise GeoOwnershipError('Geolocation belongs to another object')
        pipe.multi()
        pipe.zrem('geo:index:all', *geo_ids)
        pipe.zrem(f'geo:index:type:{obj_type}', *geo_ids)
        pipe.delete(*record_keys)
        pipe.delete(f'geo:object:{obj_gid}')
        return len(geo_ids)

    return _run_transaction(key_types, remove_all)


def object_has_geo(obj_gid):
    return get_object_nb_geos(obj_gid) > 0


def get_object_nb_geos(obj_gid):
    _validate_owner(obj_gid)
    return _get_geo_db().zcard(f'geo:object:{obj_gid}')


def get_geo_object_gid(geo_id):
    geo_id = _validate_geo_id(geo_id)
    return _get_geo_db().hget(f'geo:observation:{geo_id}', 'obj_gid')


def yield_objects_type_geos(obj_type):
    """Stream records by object type without loading the entire spatial index."""
    _validate_owner(f'{obj_type}::validation')
    db = _get_geo_db()
    for geo_id, _ in db.zscan_iter(f'geo:index:type:{obj_type}', count=100):
        geo = _decode_geo(geo_id, db.hgetall(f'geo:observation:{geo_id}'))
        if geo is not None and _validate_owner(geo['obj_gid']) == obj_type:
            yield geo


def _repair_geo_observation(geo_id, apply, owner_exists, remove_orphans):
    record_key = f'geo:observation:{geo_id}'

    def repair(pipe):
        geo = _decode_geo(geo_id, pipe.hgetall(record_key))
        if geo is None:
            pipe.multi()
            return {'state': 'missing'}
        obj_gid = geo['obj_gid']
        obj_type = _validate_owner(obj_gid)
        key_types = {f'geo:object:{obj_gid}': 'zset', 'geo:index:all': 'zset', f'geo:index:type:{obj_type}': 'zset'}
        pipe.watch(*key_types)
        _check_key_types(pipe, key_types)
        present = owner_exists(obj_gid)
        result = {'state': 'valid' if present else 'orphan', 'missing_references': 0, 'incorrect_positions': 0, 'incorrect_order': 0}
        if present:
            score = pipe.zscore(f'geo:object:{obj_gid}', geo_id)
            if score is None:
                result['missing_references'] += 1
            elif score != geo['created_at']:
                result['incorrect_order'] += 1
            for index in ('geo:index:all', f'geo:index:type:{obj_type}'):
                position = pipe.geopos(index, geo_id)[0]
                if position is None:
                    result['missing_references'] += 1
                elif abs(position[0] - geo['longitude']) > 0.00001 or abs(position[1] - get_indexed_latitude(geo['latitude'])) > 0.00001:
                    result['incorrect_positions'] += 1
        pipe.multi()
        if not present:
            if apply and remove_orphans:
                pipe.zrem(f'geo:object:{obj_gid}', geo_id)
                pipe.zrem('geo:index:all', geo_id)
                pipe.zrem(f'geo:index:type:{obj_type}', geo_id)
                pipe.delete(record_key)
            return result
        if apply:
            pipe.zadd(f'geo:object:{obj_gid}', {geo_id: geo['created_at']})
            pipe.geoadd('geo:index:all', [geo['longitude'], get_indexed_latitude(geo['latitude']), geo_id])
            pipe.geoadd(f'geo:index:type:{obj_type}', [geo['longitude'], get_indexed_latitude(geo['latitude']), geo_id])
        return result

    return _run_transaction({record_key: 'hash'}, repair)


def _repair_geo_reference(key, geo_id, apply, owner_exists):
    record_key = f'geo:observation:{geo_id}'

    def repair(pipe):
        if pipe.zscore(key, geo_id) is None:
            pipe.multi()
            return False
        geo = _decode_geo(geo_id, pipe.hgetall(record_key))
        if geo is None:
            stale = True
        else:
            obj_gid = geo['obj_gid']
            obj_type = _validate_owner(obj_gid)
            expected_keys = {f'geo:object:{obj_gid}', 'geo:index:all', f'geo:index:type:{obj_type}'}
            stale = key not in expected_keys or not owner_exists(obj_gid)
        pipe.multi()
        if stale and apply:
            pipe.zrem(key, geo_id)
        return stale

    return _run_transaction({key: 'zset', record_key: 'hash'}, repair)


def repair_geo_indexes(apply=False, owner_exists=None, remove_orphans=False):
    """Rebuild indexes from canonical records and remove stale references.

    Dry-run is the default. Canonical orphan records are deleted only with
    remove_orphans and an owner existence callback. Pause object/GEO mutations
    during maintenance: owner existence lives outside the GEO namespace.
    Invalid records and incompatible key types are reported, never guessed at.
    """
    if remove_orphans and owner_exists is None:
        raise ValueError('Removing orphan records requires an owner existence check')
    db = _get_geo_db()
    report = {'applied': bool(apply), 'observations': 0, 'valid': 0, 'orphans': 0, 'reindexed': 0,
              'missing_references': 0, 'incorrect_positions': 0, 'incorrect_order': 0, 'removed_orphans': 0,
              'references': 0, 'stale_references': 0, 'removed_references': 0, 'error_count': 0, 'errors': []}
    owners = {}

    def check_owner(obj_gid):
        if obj_gid not in owners:
            owners[obj_gid] = True if owner_exists is None else bool(owner_exists(obj_gid))
        return owners[obj_gid]

    def record_error(key, err):
        report['error_count'] += 1
        if len(report['errors']) < 100:
            report['errors'].append({'key': key, 'error': str(err)})

    for key in db.scan_iter(match='geo:observation:*', count=100):
        report['observations'] += 1
        geo_id = key.removeprefix('geo:observation:')
        try:
            if _validate_geo_id(geo_id) != geo_id:
                raise GeoStorageError('Geolocation key must use the canonical UUID4 hex ID')
            result = _repair_geo_observation(geo_id, apply, check_owner, remove_orphans)
        except (ValueError, GeoStorageError) as err:
            record_error(key, err)
            continue
        for field in ('missing_references', 'incorrect_positions', 'incorrect_order'):
            report[field] += result.get(field, 0)
        if result['state'] == 'valid':
            report['valid'] += 1
            if apply:
                report['reindexed'] += 1
        elif result['state'] == 'orphan':
            report['orphans'] += 1
            if apply and remove_orphans:
                report['removed_orphans'] += 1

    for pattern in ('geo:object:*', 'geo:index:all', 'geo:index:type:*'):
        for key in db.scan_iter(match=pattern, count=100):
            key_type = db.type(key)
            if key_type == 'none':
                continue
            if key_type != 'zset':
                record_error(key, GeoStorageError('Index or object membership must be a sorted set'))
                continue
            for geo_id, _ in db.zscan_iter(key, count=100):
                report['references'] += 1
                try:
                    stale = _repair_geo_reference(key, geo_id, apply, check_owner)
                except (ValueError, GeoStorageError) as err:
                    record_error(key, err)
                    continue
                if stale:
                    report['stale_references'] += 1
                    if apply:
                        report['removed_references'] += 1
    return report

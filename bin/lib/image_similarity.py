#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import heapq
import logging
import string
from itertools import combinations

import imagehash
from photo_dna_rs import Hash as PhotoDNAHash
from redis.exceptions import RedisError

from lib.ConfigLoader import ConfigLoader


PHASH = 'phash'
PHOTODNA = 'photodna'

PHASH_BITS = 64
PHASH_PARTITIONS = 4
PHASH_PARTITION_BITS = PHASH_BITS // PHASH_PARTITIONS
MAX_PHASH_RADIUS = 11
MIH_BUCKET_PAGE_SIZE = 512
MIH_PIPELINE_BUCKETS = 64
MIH_MAINTENANCE_BATCH_SIZE = 1000

logger = logging.getLogger(__name__)

config_loader = ConfigLoader()
r_imgsim = config_loader.get_db_conn('Kvrocks_ImageSimilarity')
PHASH_HAMMING_DISTANCE = config_loader.get_config_int('ImageSimilarity', 'phash_hamming_distance')
config_loader = None

if not 0 <= PHASH_HAMMING_DISTANCE <= MAX_PHASH_RADIUS:
    raise ValueError(f'phash_hamming_distance must be between 0 and {MAX_PHASH_RADIUS}')


def exists(image_id, algorithm):
    return bool(r_imgsim.hexists(f'image:{image_id}', algorithm))


def get_fingerprint(image_id, algorithm):
    return r_imgsim.hget(f'image:{image_id}', algorithm)


def _parse_phash(phash):
    if (not isinstance(phash, str) or len(phash) != 16
            or any(character not in string.hexdigits for character in phash)):
        raise ValueError('pHash must contain exactly 16 hexadecimal characters')
    try:
        value = int(phash, 16)
    except ValueError as err:
        raise ValueError('pHash must contain exactly 16 hexadecimal characters') from err
    if not value:
        raise ValueError('pHash 0000000000000000 is not supported')
    return value


def _split_phash(phash):
    return tuple((phash >> offset) & 0xffff
                 for offset in range(0, PHASH_BITS, PHASH_PARTITION_BITS))


def _mih_bucket_key(partition, value):
    return f'mih:phash:{partition}:{value:04x}'


def _index_phash(phash):
    for partition, value in enumerate(_split_phash(phash)):
        r_imgsim.execute_command('SIADD', _mih_bucket_key(partition, value), phash)


def delete_phash_mih():
    deleted = 0
    while True:
        deleted_in_pass = 0
        keys = []
        for key in r_imgsim.scan_iter(match='mih:phash:*', count=MIH_MAINTENANCE_BATCH_SIZE):
            keys.append(key)
            if len(keys) >= MIH_MAINTENANCE_BATCH_SIZE:
                deleted_in_pass += r_imgsim.delete(*keys)
                keys = []
        if keys:
            deleted_in_pass += r_imgsim.delete(*keys)
        deleted += deleted_in_pass
        if not deleted_in_pass:
            return deleted


def rebuild_phash_mih():
    deleted_keys = delete_phash_mih()
    indexed_phashes = 0
    skipped_fingerprints = 0
    commands = []

    def execute_commands():
        if commands:
            pipeline = r_imgsim.pipeline(transaction=False)
            for command in commands:
                pipeline.execute_command(*command)
            pipeline.execute()
            commands.clear()

    prefix = 'fingerprint:phash:'
    for key in r_imgsim.scan_iter(match=f'{prefix}*', count=MIH_MAINTENANCE_BATCH_SIZE):
        fingerprint = key[len(prefix):]
        try:
            phash = _parse_phash(fingerprint)
        except ValueError:
            skipped_fingerprints += 1
            continue
        if not r_imgsim.scard(key):
            skipped_fingerprints += 1
            continue

        for partition, value in enumerate(_split_phash(phash)):
            commands.append(('SIADD', _mih_bucket_key(partition, value), phash))
        indexed_phashes += 1
        if len(commands) >= MIH_MAINTENANCE_BATCH_SIZE:
            execute_commands()
    execute_commands()

    return {
        'deleted_keys': deleted_keys,
        'indexed_phashes': indexed_phashes,
        'skipped_fingerprints': skipped_fingerprints,
    }


def set_fingerprint(image_id, algorithm, fingerprint):
    previous = r_imgsim.hget(f'image:{image_id}', algorithm)
    if algorithm == PHASH:
        try:
            phash = _parse_phash(fingerprint)
        except ValueError as err:
            logger.error('Unable to index pHash for image %s: %s', image_id, err)
            return False
        fingerprint = f'{phash:016x}'
        if previous and previous != fingerprint:
            logger.error('Image %s is already mapped to a different pHash', image_id)
            return False
        # Repeat all writes on retry so a partial earlier insertion is repaired.
        _index_phash(phash)

    if previous and previous != fingerprint:
        r_imgsim.srem(f'fingerprint:{algorithm}:{previous}', image_id)
    r_imgsim.hset(f'image:{image_id}', algorithm, fingerprint)
    r_imgsim.sadd(f'fingerprint:{algorithm}:{fingerprint}', image_id)
    return True


def _phash_neighbors(value, radius):
    yield value
    for distance in range(1, radius + 1):
        for positions in combinations(range(PHASH_PARTITION_BITS), distance):
            mask = 0
            for position in positions:
                mask |= 1 << position
            yield value ^ mask


def _get_mih_bucket_keys(query, radius):
    local_radius = radius // PHASH_PARTITIONS
    return [
        _mih_bucket_key(partition, neighbor)
        for partition, value in enumerate(_split_phash(query))
        for neighbor in _phash_neighbors(value, local_radius)
    ]


def _get_initial_mih_pages(keys):
    pages = []
    for offset in range(0, len(keys), MIH_PIPELINE_BUCKETS):
        batch = keys[offset:offset + MIH_PIPELINE_BUCKETS]
        pipeline = r_imgsim.pipeline(transaction=False)
        for key in batch:
            pipeline.execute_command('SIRANGE', key, 0, MIH_BUCKET_PAGE_SIZE)
        pages.extend(pipeline.execute())
    return pages


def _iter_mih_bucket(key, first_page):
    page = first_page
    while page:
        for phash in page:
            yield int(phash)
        if len(page) < MIH_BUCKET_PAGE_SIZE:
            return
        page = r_imgsim.execute_command(
            'SIRANGE', key, 0, MIH_BUCKET_PAGE_SIZE, 'CURSOR', page[-1]
        )


def _iter_mih_candidates(keys):
    pages = _get_initial_mih_pages(keys)
    streams = [_iter_mih_bucket(key, page) for key, page in zip(keys, pages)]
    heap = []
    for stream_id, stream in enumerate(streams):
        try:
            heapq.heappush(heap, (next(stream), stream_id, stream))
        except StopIteration:
            pass

    previous = None
    while heap:
        candidate, stream_id, stream = heapq.heappop(heap)
        if candidate != previous:
            yield candidate
            previous = candidate
        try:
            heapq.heappush(heap, (next(stream), stream_id, stream))
        except StopIteration:
            pass


def search_phash(phash, radius):
    query = _parse_phash(phash)
    if not isinstance(radius, int) or isinstance(radius, bool) or not 0 <= radius <= MAX_PHASH_RADIUS:
        raise ValueError(f'pHash radius must be between 0 and {MAX_PHASH_RADIUS}')

    image_ids = set()
    for candidate in _iter_mih_candidates(_get_mih_bucket_keys(query, radius)):
        if (query ^ candidate).bit_count() <= radius:
            image_ids.update(get_images(PHASH, f'{candidate:016x}'))
    return sorted(image_ids)


def api_search_phash(data):
    if not isinstance(data, dict):
        return {'status': 'error', 'reason': 'JSON body must be an object'}, 400
    if 'phash' not in data:
        return {'status': 'error', 'reason': 'Missing pHash'}, 400
    if 'radius' in data or 'max_distance' in data:
        return {'status': 'error', 'reason': 'pHash Hamming distance is configured by the server'}, 400

    try:
        phash = f"{_parse_phash(data['phash']):016x}"
        images = search_phash(phash, PHASH_HAMMING_DISTANCE)
    except ValueError as err:
        return {'status': 'error', 'reason': str(err)}, 400
    except RedisError:
        return {'status': 'error', 'reason': 'Image similarity storage unavailable'}, 503

    return {
        'phash': phash,
        'hamming_distance': PHASH_HAMMING_DISTANCE,
        'images': images,
    }, 200


def search_image(image):
    if is_animated(image):
        raise ValueError('Animated images are not supported')
    phash = calculate_phash(image)
    return {
        'phash': phash,
        'hamming_distance': PHASH_HAMMING_DISTANCE,
        'images': search_phash(phash, PHASH_HAMMING_DISTANCE),
    }


def get_fingerprints(image_id):
    return r_imgsim.hgetall(f'image:{image_id}')


def get_images(algorithm, fingerprint):
    return r_imgsim.smembers(f'fingerprint:{algorithm}:{fingerprint}')


def delete(image_id):
    for algorithm, fingerprint in r_imgsim.hgetall(f'image:{image_id}').items():
        r_imgsim.srem(f'fingerprint:{algorithm}:{fingerprint}', image_id)
        if not r_imgsim.scard(f'fingerprint:{algorithm}:{fingerprint}'):
            r_imgsim.delete(f'fingerprint:{algorithm}:{fingerprint}')
    return r_imgsim.delete(f'image:{image_id}')


def get_image_similarity_meta(image_id):
    fingerprints = get_fingerprints(image_id)
    meta = {}
    for algorithm in (PHASH, PHOTODNA):
        fingerprint = fingerprints.get(algorithm)
        images = sorted(match_id for match_id in get_images(algorithm, fingerprint)
                        if match_id != image_id) if fingerprint else []
        meta[algorithm] = {'images': images}
    return meta


def is_animated(image):
    return bool(getattr(image, 'is_animated', False))


def calculate_phash(image):
    return str(imagehash.phash(image))


def calculate_photodna(image):
    rgb_image = image.convert('RGB')
    pixels = list(rgb_image.getdata())
    fingerprint = PhotoDNAHash.from_rgb_pixels(rgb_image.width, rgb_image.height, pixels)
    return fingerprint.to_hex_str()

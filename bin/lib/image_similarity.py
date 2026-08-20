#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import imagehash
from photo_dna_rs import Hash as PhotoDNAHash

from lib.ConfigLoader import ConfigLoader


PHASH = 'phash'
PHOTODNA = 'photodna'

config_loader = ConfigLoader()
r_imgsim = config_loader.get_db_conn('Kvrocks_ImageSimilarity')
config_loader = None


def exists(image_id, algorithm):
    return bool(r_imgsim.hexists(f'image:{image_id}', algorithm))


def get_fingerprint(image_id, algorithm):
    return r_imgsim.hget(f'image:{image_id}', algorithm)


def set_fingerprint(image_id, algorithm, fingerprint):
    previous = r_imgsim.hget(f'image:{image_id}', algorithm)
    if previous and previous != fingerprint:
        r_imgsim.srem(f'fingerprint:{algorithm}:{previous}', image_id)
    result = r_imgsim.hset(f'image:{image_id}', algorithm, fingerprint)
    r_imgsim.sadd(f'fingerprint:{algorithm}:{fingerprint}', image_id)
    return result


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

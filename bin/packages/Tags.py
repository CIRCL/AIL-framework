#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import redis

import Flask_config

from pytaxonomies import Taxonomies
from pymispgalaxies import Galaxies, Clusters

r_serv_tags = Flask_config.r_serv_tags

def get_taxonomie_from_tag(tag):
    return tag.split(':')[0]

def get_galaxy_from_tag(tag):
    galaxy = tag.split(':')[1]
    galaxy = galaxy.split('=')[0]
    return galaxy

def get_active_taxonomies():
    return r_serv_tags.smembers('active_taxonomies')

def get_active_galaxies():
    return r_serv_tags.smembers('active_galaxies')

def is_taxonomie_tag_enabled(taxonomie, tag):
    if tag in r_serv_tags.smembers('active_tag_' + taxonomie):
        return True
    else:
        return False

def is_galaxy_tag_enabled(galaxy, tag):
    if tag in r_serv_tags.smembers('active_tag_galaxies_' + galaxy):
        return True
    else:
        return False

# Check if tags are enabled in AIL
def is_valid_tags_taxonomies_galaxy(list_tags, list_tags_galaxy):
    print(list_tags)
    print(list_tags_galaxy)
    if list_tags:
        active_taxonomies = get_active_taxonomies()

        for tag in list_tags:
            taxonomie = get_taxonomie_from_tag(tag)
            if taxonomie not in active_taxonomies:
                return False
            if not is_taxonomie_tag_enabled(taxonomie, tag):
                return False

    if list_tags_galaxy:
        active_galaxies = get_active_galaxies()

        for tag in list_tags_galaxy:
            galaxy = get_galaxy_from_tag(tag)
            if galaxy not in active_galaxies:
                return False
            if not is_galaxy_tag_enabled(galaxy, tag):
                return False
    return True

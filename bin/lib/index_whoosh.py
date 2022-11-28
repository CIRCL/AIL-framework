#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from shutil import rmtree

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
INDEX_PATH = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Indexer", "path"))
all_index_file = os.path.join(INDEX_PATH, 'all_index.txt')
config_loader = None

def get_first_index_name():
    with open(all_index_file) as f:
        first_index = f.readline().replace('\n', '')
    return first_index

def get_last_index_name():
    with open(all_index_file) as f:
        for line in f: # # FIXME: replace by tail ?
            pass
        last_index = line.replace('\n', '')
    return last_index

def get_all_index():
    all_index = []
    with open(all_index_file) as f:
        for line in f:
            line = line.replace('\n', '')
            if line:
                all_index.append(line)
    return all_index

def get_index_full_path(index_name):
    return os.path.join(INDEX_PATH, index_name)

# remove empty line
def check_index_list_integrity():
    with open(all_index_file, 'r') as f:
        lines = f.readlines()
    with open(all_index_file, 'w') as f:
        for line in lines:
            if line != '\n':
                f.write(line)

def _remove_index_name_from_all_index(index_name):
    with open(all_index_file, 'r') as f:
        lines = f.readlines()
    with open(all_index_file, 'w') as f:
        for line in lines:
            if line.replace('\n', '') != index_name:
                f.write(line)

def delete_index_by_name(index_name):
    index_path = get_index_full_path(index_name)
    index_path = os.path.realpath(index_path)
    # incorrect filename
    if not os.path.commonprefix([index_path, INDEX_PATH]) == INDEX_PATH:
        raise Exception(f'Path traversal detected {index_path}')
    if not os.path.isdir(index_path):
        print('Error: The index directory {index_path} doesn\'t exist')
        return None
    res = rmtree(index_path)
    _remove_index_name_from_all_index(index_name)

def delete_first_index():
    index_name = get_first_index_name()
    delete_index_by_name(index_name)

def delete_last_index():
    index_name = get_last_index_name()
    delete_index_by_name(index_name)

#### DATA RETENTION ####

#keep time most recent index
def delete_older_index_by_time(int_time):
    all_index = get_all_index()
    if all_index:
        if int(all_index[-1]) > int_time: # make sure to keep one files
            for index_name in all_index:
                if int(index_name) < int_time:
                    print(f'deleting index {index_name} ...')
                    delete_index_by_name(index_name)

# keep x most recent index
def delete_older_index(number_of_index_to_keep):
    if number_of_index_to_keep > 1:
        all_index = get_all_index()
        if len(get_all_index()) > number_of_index_to_keep:
            for index_name in all_index[0:-number_of_index_to_keep]:
                print(f'deleting index {index_name} ...')
                delete_index_by_name(index_name)

##-- DATA RETENTION  --##

# if __name__ == '__main__':
#     delete_older_index(3)

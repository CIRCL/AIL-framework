#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import ssdeep
import sys
import time
import tlsh

import datetime

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_serv_db = config_loader.get_db_conn("Kvrocks_DB")
MIN_ITEM_SIZE = float(config_loader.get_config_str('Modules_Duplicates', 'min_paste_size')) # # TODO: RENAME ME
config_loader = None

#
#
# Hash != Duplicates => New correlation HASH => check if same hash if duplicate == 100
#
# Object Hash => correlation decoded => don't need correlation to exists
#
# New CORRELATION => HASH
#                     -> compute/get(if exist we have a correlation) hash -> get correlation same hash
#
#
# Duplicates between differents objects ?????
#         Diff Decoded -> Item => Diff Item decoded - Item
#
# Duplicates domains != Duplicates items



def get_ssdeep_hash(content):
    return ssdeep.hash(content)

def get_ssdeep_similarity(obj_hash, other_hash):
    return ssdeep.compare(obj_hash, other_hash)

def get_tlsh_hash(content):
    return tlsh.hash(content)

def get_tlsh_similarity(obj_hash, other_hash):
    similarity = tlsh.diffxlen(obj_hash, other_hash)
    if similarity > 100:
        similarity = 100
    similarity = 100 - similarity
    return similarity

def get_algo_similarity(algo, obj_hash, other_hash):
    if algo == 'ssdeep':
        return get_ssdeep_similarity(obj_hash, other_hash)
    elif algo == 'tlsh':
        return get_tlsh_similarity(obj_hash, other_hash)

def get_algo_hashs_by_month(algo, date_ymonth):
    return r_serv_db.hkeys(f'duplicates:hashs:{algo}:{date_ymonth}')

def exists_algo_hash_by_month(algo, hash, date_ymonth):
    return r_serv_db.hexists(f'duplicates:hashs:{algo}:{date_ymonth}', hash)

def get_object_id_by_hash(algo, hash, date_ymonth):
    return r_serv_db.hget(f'duplicates:hashs:{algo}:{date_ymonth}', hash)

def save_object_hash(algo, date_ymonth, hash, obj_id):
    r_serv_db.hset(f'duplicates:hashs:{algo}:{date_ymonth}', hash, obj_id)


def get_duplicates(obj_type, subtype, id):
    dict_dup = {}
    duplicates = r_serv_db.smembers(f'obj:duplicates:{obj_type}:{subtype}:{id}')
    for str_dup in duplicates:
        similarity, algo, id = str_dup.split(':', 2)
        if not dict_dup.get(id):
            dict_dup[id] = []
        dict_dup[id].append({'algo': algo, 'similarity': int(similarity)})
    return dict_dup


def _add_obj_duplicate(algo, similarity, obj_type, subtype, id, id_2):
    r_serv_db.sadd(f'obj:duplicates:{obj_type}:{subtype}:{id}', f'{similarity}:{algo}:{id_2}')

def add_obj_duplicate(algo, hash, similarity, obj_type, subtype, id, date_ymonth):
    obj2_id = get_object_id_by_hash(algo, hash, date_ymonth)
    # same content
    if similarity == 100:
        dups = get_duplicates(obj_type, subtype, id)
        for dup_id in dups:
            for algo_dict in dups[dup_id]:
                if algo_dict['similarity'] == 100 and algo_dict['algo'] == algo:
                    _add_obj_duplicate(algo, similarity, obj_type, subtype, id, dups[dup_id])
                    _add_obj_duplicate(algo, similarity, obj_type, subtype, dups[dup_id], id)
    _add_obj_duplicate(algo, similarity, obj_type, subtype, id, obj2_id)
    _add_obj_duplicate(algo, similarity, obj_type, subtype, obj2_id, id)




def get_last_x_month_dates(nb_months):
    now = datetime.datetime.now()
    result = [now.strftime("%Y%m")]
    for x in range(0, nb_months):
        now = now.replace(day=1) - datetime.timedelta(days=1)
        result.append(now.strftime("%Y%m"))
    return result



if __name__ == '__main__':
    res = get_last_x_month_dates(7)
    print(res)












#################################

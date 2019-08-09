#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import time
import uuid
import redis
import datetime

from collections import defaultdict

from nltk.tokenize import RegexpTokenizer
from textblob import TextBlob

sys.path.append(os.path.join(os.environ['AIL_FLASK'], 'modules'))
import Flask_config

r_serv_term = Flask_config.r_serv_term
email_regex = Flask_config.email_regex

special_characters = set('[<>~!?@#$%^&*|()_-+={}":;,.\'\n\r\t]/\\')
special_characters.add('\\s')

# NLTK tokenizer
tokenizer = RegexpTokenizer('[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\/\-/\=\'\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]+',
                                    gaps=True, discard_empty=True)

def is_valid_uuid_v4(UUID):
    UUID = UUID.replace('-', '')
    try:
        uuid_test = uuid.UUID(hex=UUID, version=4)
        return uuid_test.hex == UUID
    except:
        return False

# # TODO: use new package => duplicate fct
def is_in_role(user_id, role):
    if r_serv_db.sismember('user_role:{}'.format(role), user_id):
        return True
    else:
        return False

def check_term_uuid_valid_access(term_uuid, user_id):
    if not is_valid_uuid_v4(term_uuid):
        return ({"status": "error", "reason": "Invalid uuid"}, 400)
    level = r_serv_term.hget('tracked_term:{}'.format(term_uuid), 'level')
    if not level:
        return ({"status": "error", "reason": "Unknown uuid"}, 404)
    if level == 0:
        if r_serv_term.hget('tracked_term:{}'.format(term_uuid), 'user_id') != user_id:
            if not is_in_role(user_id, 'admin'):
                return ({"status": "error", "reason": "Unknown uuid"}, 404)
    return None


def is_valid_mail(email):
    result = email_regex.match(email)
    if result:
        return True
    else:
        return False

def verify_mail_list(mail_list):
    for mail in mail_list:
        if not is_valid_mail(mail):
            return ({'status': 'error', 'reason': 'Invalid email', 'value': mail}, 400)
    return None

def is_valid_regex(term_regex):
    try:
        re.compile(term_regex)
        return True
    except:
        return False

def get_text_word_frequency(item_content, filtering=True):
    item_content = item_content.lower()
    words_dict = defaultdict(int)

    if filtering:
        blob = TextBlob(item_content , tokenizer=tokenizer)
    else:
        blob = TextBlob(item_content)
    for word in blob.tokens:
        words_dict[word] += 1
    return words_dict

# # TODO: create all tracked words
def get_tracked_words_list():
    return list(r_serv_term.smembers('all:tracked_term:word'))

def get_set_tracked_words_list():
    set_list = r_serv_term.smembers('all:tracked_term:set')
    all_set_list = []
    for elem in set_list:
        res = elem.split(';')
        num_words = int(res[1])
        ter_set = res[0].split(',')
        all_set_list.append((ter_set, num_words, elem))
    return all_set_list

def get_regex_tracked_words_dict():
    regex_list = r_serv_term.smembers('all:tracked_term:regex')
    dict_tracked_regex = {}
    for regex in regex_list:
        dict_tracked_regex[regex] = re.compile(regex)
    return dict_tracked_regex

def get_tracked_term_list_item(term_uuid, date_from, date_to):
    all_item_id = []
    if date_from and date_to:
        for date in r_serv_term.zrangebyscore('tracked_term:stat:{}'.format(term_uuid), int(date_from), int(date_to)):
            all_item_id = all_item_id + list(r_serv_term.smembers('tracked_term:item:{}:{}'.format(term_uuid, date)))
    return all_item_id

def is_term_tracked_in_global_level(term, term_type):
    res = r_serv_term.smembers('all:tracked_term_uuid:{}:{}'.format(term_type, term))
    if res:
        for elem_uuid in res:
            if r_serv_term.hget('tracked_term:{}'.format(elem_uuid), 'level')=='1':
                return True
    return False

def is_term_tracked_in_user_level(term, term_type, user_id):
    res = r_serv_term.smembers('user:tracked_term:{}'.format(user_id))
    if res:
        for elem_uuid in res:
            if r_serv_term.hget('tracked_term:{}'.format(elem_uuid), 'tracked')== term:
                if r_serv_term.hget('tracked_term:{}'.format(elem_uuid), 'type')== term_type:
                    return True
    return False

def parse_json_term_to_add(dict_input, user_id):
    term = dict_input.get('term', None)
    if not term:
        return ({"status": "error", "reason": "Term not provided"}, 400)
    term_type = dict_input.get('type', None)
    if not term_type:
        return ({"status": "error", "reason": "Term type not provided"}, 400)
    nb_words = dict_input.get('nb_words', 1)

    res = parse_tracked_term_to_add(term , term_type, nb_words=nb_words)
    if res[1]!=200:
        return res
    term = res[0]['term']
    term_type = res[0]['type']

    tags = dict_input.get('tags', [])
    mails = dict_input.get('mails', [])
    res = verify_mail_list(mails)
    if res:
        return res

    ## TODO: add dashboard key
    level = dict_input.get('level', 1)
    try:
        level = int(level)
        if level not in range(0, 1):
            level = 1
    except:
        level = 1

    # check if term already tracked in global
    if level==1:
        if is_term_tracked_in_global_level(term, term_type):
            return ({"status": "error", "reason": "Term already tracked"}, 409)
    else:
        if is_term_tracked_in_user_level(term, term_type, user_id):
            return ({"status": "error", "reason": "Term already tracked"}, 409)

    term_uuid = add_tracked_term(term , term_type, user_id, level, tags, mails)

    return ({'term': term, 'type': term_type, 'uuid': term_uuid}, 200)


def parse_tracked_term_to_add(term , term_type, nb_words=1):
    if term_type=='regex':
        if not is_valid_regex(term):
            return ({"status": "error", "reason": "Invalid regex"}, 400)
    elif term_type=='word' or term_type=='set':
        # force lowercase
        term = term.lower()
        word_set = set(term)
        set_inter = word_set.intersection(special_characters)
        if set_inter:
            return ({"status": "error", "reason": "special character not allowed", "message": "Please use a regex or remove all special characters"}, 400)
        words = term.split()
        # not a word
        if term_type=='word' and len(words)>1:
            term_type = 'set'

        # ouput format: term1,term2,term3;2
        if term_type=='set':
            try:
                nb_words = int(nb_words)
            except:
                nb_words = 1
            if nb_words==0:
                nb_words = 1

            words_set = set(words)
            words_set = sorted(words_set)

            term = ",".join(words_set)
            term = "{};{}".format(term, nb_words)

            if nb_words > len(words_set):
                nb_words = len(words_set)

    else:
        return ({"status": "error", "reason": "Incorrect type"}, 400)
    return ({"status": "success", "term": term, "type": term_type}, 200)

def add_tracked_term(term , term_type, user_id, level, tags, mails, dashboard=0):

    term_uuid =  str(uuid.uuid4())

    # create metadata
    r_serv_term.hset('tracked_term:{}'.format(term_uuid), 'tracked',term)
    r_serv_term.hset('tracked_term:{}'.format(term_uuid), 'type', term_type)
    r_serv_term.hset('tracked_term:{}'.format(term_uuid), 'date', datetime.date.today().strftime("%Y%m%d"))
    r_serv_term.hset('tracked_term:{}'.format(term_uuid), 'user_id', user_id)
    r_serv_term.hset('tracked_term:{}'.format(term_uuid), 'level', level)
    r_serv_term.hset('tracked_term:{}'.format(term_uuid), 'dashboard', dashboard)

    # create all term set
    r_serv_term.sadd('all:tracked_term:{}'.format(term_type), term)

    # create term - uuid map
    r_serv_term.sadd('all:tracked_term_uuid:{}:{}'.format(term_type, term), term_uuid)

    # add display level set
    if level == 0: # user only
        r_serv_term.sadd('user:tracked_term:{}'.format(user_id), term_uuid)
    elif level == 1: # global
        r_serv_term.sadd('gobal:tracked_term', term_uuid)

    # create term tags list
    for tag in tags:
        r_serv_term.sadd('tracked_term:tags:{}'.format(term_uuid), tag)

    # create term tags mail notification list
    for mail in mails:
        r_serv_term.sadd('tracked_term:mail:{}'.format(term_uuid), mail)

    # toggle refresh module tracker list/set
    r_serv_term.set('tracked_term:refresh:{}'.format(term_type), time.time())

    return term_uuid

def parse_tracked_term_to_delete(dict_input, user_id):
    res = check_term_uuid_valid_access(term_uuid, user_id)
    if res:
        return res

    delete_term(term_uuid)
    return ({"uuid": term_uuid}, 200)

def delete_term(term_uuid):
    term = r_serv_term.hget('tracked_term:{}'.format(term_uuid), 'tracked')
    term_type = r_serv_term.hget('tracked_term:{}'.format(term_uuid), 'type')
    level = r_serv_term.hget('tracked_term:{}'.format(term_uuid), 'level')
    r_serv_term.srem('all:tracked_term_uuid:{}:{}'.format(term_type, term), term_uuid)
    # Term not tracked by other users
    if not r_serv_term.exists('all:tracked_term_uuid:{}:{}'.format(term_type, term)):
        r_serv_term.srem('all:tracked_term:{}'.format(term_type), term)

        # toggle refresh module tracker list/set
        r_serv_term.set('tracked_term:refresh:{}'.format(term_type), time.time())

    if level == 0: # user only
        user_id = term_type = r_serv_term.hget('tracked_term:{}'.format(term_uuid), 'user_id')
        r_serv_term.srem('user:tracked_term:{}'.format(user_id), term_uuid)
    elif level == 1: # global
        r_serv_term.srem('gobal:tracked_term', term_uuid)

    # delete metatadata
    r_serv_term.delete('tracked_term:{}'.format(term_uuid))

    # remove tags
    r_serv_term.delete('tracked_term:tags:{}'.format(term_uuid))

    # remove mails
    r_serv_term.delete('tracked_term:mail:{}'.format(term_uuid))

    # remove item set
    all_item_date = r_serv_term.zrange('tracked_term:stat:{}'.format(term_uuid), 0, -1)
    for date in all_item_date:
        r_serv_term.delete('tracked_term:item:{}:{}'.format(term_uuid, date))
    r_serv_term.delete('tracked_term:stat:{}'.format(term_uuid))

def get_term_uuid_list(term, term_type):
    return list(r_serv_term.smembers('all:tracked_term_uuid:{}:{}'.format(term_type, term)))

def get_term_tags(term_uuid):
    return list(r_serv_term.smembers('tracked_term:tags:{}'.format(term_uuid)))

def get_term_mails(term_uuid):
    return list(r_serv_term.smembers('tracked_term:mail:{}'.format(term_uuid)))

def add_tracked_item(term_uuid, item_id, item_date):
    # track item
    r_serv_term.sadd('tracked_term:item:{}:{}'.format(term_uuid, item_date), item_id)
    # track nb item by date
    r_serv_term.zadd('tracked_term:stat:{}'.format(term_uuid), item_date, int(item_date))

def create_token_statistics(item_date, word, nb):
    r_serv_term.zincrby('stat_token_per_item_by_day:{}'.format(item_date), word, 1)
    r_serv_term.zincrby('stat_token_total_by_day:{}'.format(item_date), word, nb)
    r_serv_term.sadd('stat_token_history', item_date)

def delete_token_statistics_by_date(item_date):
    r_serv_term.delete('stat_token_per_item_by_day:{}'.format(item_date))
    r_serv_term.delete('stat_token_total_by_day:{}'.format(item_date))
    r_serv_term.srem('stat_token_history', item_date)

def get_all_token_stat_history():
    return r_serv_term.smembers('stat_token_history')

def get_tracked_term_last_updated_by_type(term_type):
    epoch_update = r_serv_term.get('tracked_term:refresh:{}'.format(term_type))
    if not epoch_update:
        epoch_update = 0
    return float(epoch_update)

def parse_get_tracker_term_item(dict_input, user_id):
    term_uuid = dict_input.get('uuid', None)
    res = check_term_uuid_valid_access(term_uuid, user_id)
    if res:
        return res


    date_from = dict_input.get('date_from', None)
    date_to = dict_input.get('date_to', None)

    if date_from is None:
        date_from = r_serv_term.zrevrange('tracked_term:stat:{}'.format(term_uuid), 0, 0)
        if date_from:
            date_from = date_from[0]

    if date_to is None:
        date_to = date_from

    if date_from > date_to:
        date_from = date_to

    all_item_id = get_tracked_term_list_item(term_uuid, date_from, date_to)

    res_dict = {}
    res_dict['uuid'] = term_uuid
    res_dict['date_from'] = date_from
    res_dict['date_to'] = date_to
    res_dict['items'] = all_item_id
    return (res_dict, 200)






























def get_global_tracked_term():
    dict_tracked = {}
    tracked_set =  list(r_serv_term.smembers('global:TrackedSetSet'))
    tracked_regex = list(r_serv_term.smembers('global:TrackedRegexSet'))
    tracked_terms = list(r_serv_term.smembers('global:TrackedSetTermSet'))
    return {'term': tracked_terms, 'set': tracked_terms, 'regex': tracked_regex}

def get_user_tracked_term(user_id):
    dict_tracked = {}
    tracked_set =  list(r_serv_term.smembers('user:{}:TrackedSetSet'.format(user_id)))
    tracked_regex = list(r_serv_term.smembers('user:{}:TrackedRegexSet').format(user_id))
    tracked_terms = list(r_serv_term.smembers('user:{}:TrackedSetTermSet').format(user_id))
    return {'term': tracked_terms, 'set': tracked_terms, 'regex': tracked_regex}

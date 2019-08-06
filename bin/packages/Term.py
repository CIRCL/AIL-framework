#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import uuid
import redis
import datetime

from collections import defaultdict

from nltk.tokenize import RegexpTokenizer
from textblob import TextBlob

sys.path.append(os.path.join(os.environ['AIL_FLASK'], 'modules'))
import Flask_config

r_serv_term = Flask_config.r_serv_term

special_characters = set('[<>~!?@#$%^&*|()_-+={}":;,.\'\n\r\t]/\\')
special_characters.add('\\s')

# NLTK tokenizer
tokenizer = RegexpTokenizer('[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\/\-/\=\'\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]+',
                                    gaps=True, discard_empty=True)

def get_text_word_frequency(item_content, filtering=True):
    item_content = item_content.lower()
    words_dict = defaultdict(int)

    if filtering:
        blob = TextBlob(item_content , tokenizer=tokenizer)
    else:
        blob = TextBlob(item_content)
    for word in blob.tokens:
        words_dict[word] += 1
    print(words_dict)
    return words_dict

# # TODO: create all tracked words
def get_tracked_words_list():
    return list(r_serv_term.smembers('all:tracked_term:word'))

def get_set_tracked_words_list():
    set_list = r_serv_term.smembers('all:tracked_term:set')
    all_set_list = []
    for elem in set_list:
        elem = elem.split(';')
        num_words = int(elem[1])
        ter_set = elem[0].split(',')
        all_set_list.append((ter_set, num_words))

def parse_json_term_to_add(dict_input):
    term = dict_input.get('term', None)
    if not term:
        return ({"status": "error", "reason": "Term not provided"}, 400)
    term_type = dict_input.get('term', None)
    if not term_type:
        return ({"status": "error", "reason": "Term type not provided"}, 400)
    nb_words = dict_input.get('nb_words', 1)

    res = parse_tracked_term_to_add(term , term_type, nb_words=nb_words)
    if res['status']=='error':
        return res

    # get user_id
    tags = dict_input.get('tags', [])
    mails = dict_input.get('mails', [])
    ## TODO: verify mail integrity

    ## TODO: add dashboard key
    level = dict_input.get('level', 1)
    try:
        level = int(level)
        if level not in range(0, 1):
            level = 1
    except:
        level = 1

    term_uuid = add_tracked_term(term , term_type, user_id, level, tags, mails)

    return ({'term': term, 'uuid': term_uuid}, 200)


def parse_tracked_term_to_add(term , term_type, nb_words=1):

    # todo verify regex format
    if term_type=='regex':
        # TODO: verify regex integrity
        pass
    elif term_type=='word' or term_type=='set':
        # force lowercase
        term = term.lower()
        word_set = set(term)
        set_inter = word_set.intersection(special_characters)
        if set_inter:
            return ({"status": "error", "reason": "special character not allowed", "message": "Please use a regex or remove all special characters"}, 400)
        words = term.split()
        # not a word
        if term_type=='word' and words:
            term_type = 'set'

        # ouput format: term1,term2,term3;2
        if term_type=='set':
            try:
                nb_words = int(nb_words)
            except:
                nb_words = 1

            words_set = set(words)
            words_set = sorted(words_set)
            term = ",".join(words_set)
            term = "{};{}".format(term, nb_words)

        print(term)
        print(term_type)

        return ({"status": "success", "term": term, "type": term_type}, 200)

    else:
        return ({"status": "error", "reason": "Incorrect type"}, 400)

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
    r_serv_term.sadd('all:tracked_term_uuid:{}'.format(term), term_uuid)

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

    return term_uuid

def get_term_uuid_list(term):
    return list(r_serv_term.smembers('all:tracked_term_uuid:{}'.format(term)))



































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

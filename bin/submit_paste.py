#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import configparser
import os
import sys
import gzip
import io
import redis
import base64
import datetime
import time

from sflock.main import unpack
import sflock

from Helper import Process
from pubsublogger import publisher

def create_paste(uuid, paste_content, ltags, ltagsgalaxies, name):

    now = datetime.datetime.now()
    save_path = 'submitted/' + now.strftime("%Y") + '/' + now.strftime("%m") + '/' + now.strftime("%d") + '/' + name + '.gz'

    full_path = filename = os.path.join(os.environ['AIL_HOME'],
                            p.config.get("Directories", "pastes"), save_path)

    if os.path.isfile(full_path):
        addError(uuid, 'File: ' + save_path + ' already exist in submitted pastes')
        return 1

    try:
        gzipencoded = gzip.compress(paste_content)
        gzip64encoded = base64.standard_b64encode(gzipencoded).decode()
    except:
        abord_file_submission(uuid, "file error")
        return 1

    # use relative path
    rel_item_path = save_path.replace(PASTES_FOLDER, '', 1)

    # send paste to Global module
    relay_message = "{0} {1}".format(rel_item_path, gzip64encoded)
    p.populate_set_out(relay_message, 'Mixer')

    # increase nb of paste by feeder name
    r_serv_log_submit.hincrby("mixer_cache:list_feeder", "submitted", 1)

    # add tags
    add_tags(ltags, ltagsgalaxies, rel_item_path)

    r_serv_log_submit.incr(uuid + ':nb_end')
    r_serv_log_submit.incr(uuid + ':nb_sucess')

    if r_serv_log_submit.get(uuid + ':nb_end') == r_serv_log_submit.get(uuid + ':nb_total'):
        r_serv_log_submit.set(uuid + ':end', 1)

    print('    {} send to Global'.format(rel_item_path))
    r_serv_log_submit.sadd(uuid + ':paste_submit_link', rel_item_path)

    curr_date = datetime.date.today()
    serv_statistics.hincrby(curr_date.strftime("%Y%m%d"),'submit_paste', 1)

    return 0

def addError(uuid, errorMessage):
    print(errorMessage)
    error = r_serv_log_submit.get(uuid + ':error')
    if error != None:
        r_serv_log_submit.set(uuid + ':error', error + '<br></br>' + errorMessage)
    r_serv_log_submit.incr(uuid + ':nb_end')

def abord_file_submission(uuid, errorMessage):
    addError(uuid, errorMessage)
    r_serv_log_submit.set(uuid + ':end', 1)
    curr_date = datetime.date.today()
    serv_statistics.hincrby(curr_date.strftime("%Y%m%d"),'submit_abord', 1)
    remove_submit_uuid(uuid)


def remove_submit_uuid(uuid):
    # save temp value on disk
    r_serv_db.delete(uuid + ':ltags')
    r_serv_db.delete(uuid + ':ltagsgalaxies')
    r_serv_db.delete(uuid + ':paste_content')
    r_serv_db.delete(uuid + ':isfile')
    r_serv_db.delete(uuid + ':password')

    r_serv_log_submit.expire(uuid + ':end', expire_time)
    r_serv_log_submit.expire(uuid + ':processing', expire_time)
    r_serv_log_submit.expire(uuid + ':nb_total', expire_time)
    r_serv_log_submit.expire(uuid + ':nb_sucess', expire_time)
    r_serv_log_submit.expire(uuid + ':nb_end', expire_time)
    r_serv_log_submit.expire(uuid + ':error', expire_time)
    r_serv_log_submit.srem(uuid + ':paste_submit_link', '')
    r_serv_log_submit.expire(uuid + ':paste_submit_link', expire_time)

    # delete uuid
    r_serv_db.srem('submitted:uuid', uuid)
    print('{} all file submitted'.format(uuid))

def get_item_date(item_filename):
    l_directory = item_filename.split('/')
    return '{}{}{}'.format(l_directory[-4], l_directory[-3], l_directory[-2])

def add_item_tag(tag, item_path):
    item_date = int(get_item_date(item_path))

    #add tag
    r_serv_metadata.sadd('tag:{}'.format(item_path), tag)
    r_serv_tags.sadd('{}:{}'.format(tag, item_date), item_path)

    r_serv_tags.hincrby('daily_tags:{}'.format(item_date), tag, 1)

    tag_first_seen = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen')
    if tag_first_seen is None:
        tag_first_seen = 99999999
    else:
        tag_first_seen = int(tag_first_seen)
    tag_last_seen = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen')
    if tag_last_seen is None:
        tag_last_seen = 0
    else:
        tag_last_seen = int(tag_last_seen)

    #add new tag in list of all used tags
    r_serv_tags.sadd('list_tags', tag)

    # update fisrt_seen/last_seen
    if item_date < tag_first_seen:
        r_serv_tags.hset('tag_metadata:{}'.format(tag), 'first_seen', item_date)

    # update metadata last_seen
    if item_date > tag_last_seen:
        r_serv_tags.hset('tag_metadata:{}'.format(tag), 'last_seen', item_date)

def add_tags(tags, tagsgalaxies, path):
    list_tag = tags.split(',')
    list_tag_galaxies = tagsgalaxies.split(',')

    if list_tag != ['']:
        for tag in list_tag:
            add_item_tag(tag, path)

    if list_tag_galaxies != ['']:
        for tag in list_tag_galaxies:
            add_item_tag(tag, path)

def verify_extention_filename(filename):
    if not '.' in filename:
        return True
    else:
        file_type = filename.rsplit('.', 1)[1]

        #txt file
        if file_type in ALLOWED_EXTENSIONS:
            return True
        else:
            return False

if __name__ == "__main__":

    publisher.port = 6380
    publisher.channel = "Script"

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    r_serv_db = redis.StrictRedis(
        host=cfg.get("ARDB_DB", "host"),
        port=cfg.getint("ARDB_DB", "port"),
        db=cfg.getint("ARDB_DB", "db"),
        decode_responses=True)

    r_serv_log_submit = redis.StrictRedis(
        host=cfg.get("Redis_Log_submit", "host"),
        port=cfg.getint("Redis_Log_submit", "port"),
        db=cfg.getint("Redis_Log_submit", "db"),
        decode_responses=True)

    r_serv_tags = redis.StrictRedis(
        host=cfg.get("ARDB_Tags", "host"),
        port=cfg.getint("ARDB_Tags", "port"),
        db=cfg.getint("ARDB_Tags", "db"),
        decode_responses=True)

    r_serv_metadata = redis.StrictRedis(
        host=cfg.get("ARDB_Metadata", "host"),
        port=cfg.getint("ARDB_Metadata", "port"),
        db=cfg.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    serv_statistics = redis.StrictRedis(
        host=cfg.get('ARDB_Statistics', 'host'),
        port=cfg.getint('ARDB_Statistics', 'port'),
        db=cfg.getint('ARDB_Statistics', 'db'),
        decode_responses=True)

    expire_time = 120
    MAX_FILE_SIZE = 1000000000
    ALLOWED_EXTENSIONS = ['txt', 'sh', 'pdf']

    config_section = 'submit_paste'
    p = Process(config_section)

    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "pastes")) + '/'

    while True:

        # paste submitted
        if r_serv_db.scard('submitted:uuid') > 0:
            uuid = r_serv_db.srandmember('submitted:uuid')

            # get temp value save on disk
            ltags = r_serv_db.get(uuid + ':ltags')
            ltagsgalaxies = r_serv_db.get(uuid + ':ltagsgalaxies')
            paste_content = r_serv_db.get(uuid + ':paste_content')
            isfile = r_serv_db.get(uuid + ':isfile')
            password = r_serv_db.get(uuid + ':password')

            # needed if redis is restarted
            r_serv_log_submit.set(uuid + ':end', 0)
            r_serv_log_submit.set(uuid + ':processing', 0)
            r_serv_log_submit.set(uuid + ':nb_total', -1)
            r_serv_log_submit.set(uuid + ':nb_end', 0)
            r_serv_log_submit.set(uuid + ':nb_sucess', 0)
            r_serv_log_submit.set(uuid + ':error', 'error:')
            r_serv_log_submit.sadd(uuid + ':paste_submit_link', '')


            r_serv_log_submit.set(uuid + ':processing', 1)

            if isfile == 'True':
                file_full_path = paste_content

                if not os.path.exists(file_full_path):
                    abord_file_submission(uuid, "Server Error, the archive can't be found")
                    continue

                #verify file lengh
                if os.stat(file_full_path).st_size > MAX_FILE_SIZE:
                    abord_file_submission(uuid, 'File :{} too large'.format(file_full_path))

                else:
                    filename = file_full_path.split('/')[-1]
                    if not '.' in filename:
                        # read file
                        try:
                            with open(file_full_path,'r') as f:
                                content = f.read()
                        except:
                            abord_file_submission(uuid, "file error")
                            continue
                        r_serv_log_submit.set(uuid + ':nb_total', 1)
                        create_paste(uuid, content.encode(), ltags, ltagsgalaxies, uuid)
                        remove_submit_uuid(uuid)

                    else:
                        file_type = filename.rsplit('.', 1)[1]

                        #txt file
                        if file_type in ALLOWED_EXTENSIONS:
                            with open(file_full_path,'r') as f:
                                content = f.read()
                            r_serv_log_submit.set(uuid + ':nb_total', 1)
                            create_paste(uuid, content.encode(), ltags, ltagsgalaxies, uuid)
                            remove_submit_uuid(uuid)
                        #compressed file
                        else:
                            #decompress file
                            try:
                                if password == '':
                                    files = unpack(file_full_path.encode())
                                    #print(files.children)
                                else:
                                    try:
                                        files = unpack(file_full_path.encode(), password=password.encode())
                                        #print(files.children)
                                    except sflock.exception.IncorrectUsageException:
                                        abord_file_submission(uuid, "Wrong Password")
                                        continue
                                    except:
                                        abord_file_submission(uuid, "file decompression error")
                                        continue
                                print('unpacking {} file'.format(files.unpacker))
                                if(not files.children):
                                    abord_file_submission(uuid, "Empty compressed file")
                                    continue
                                # set number of files to submit
                                r_serv_log_submit.set(uuid + ':nb_total', len(files.children))
                                n = 1
                                for child in files.children:
                                    if verify_extention_filename(child.filename.decode()):
                                        create_paste(uuid, child.contents, ltags, ltagsgalaxies, uuid+'_'+ str(n) )
                                        n = n + 1
                                    else:
                                        print('bad extention')
                                        addError(uuid, 'Bad file extension: {}'.format(child.filename.decode()) )

                            except FileNotFoundError:
                                print('file not found')
                                addError(uuid, 'File not found: {}'.format(file_full_path), uuid )

                            remove_submit_uuid(uuid)



            # textarea input paste
            else:
                r_serv_log_submit.set(uuid + ':nb_total', 1)
                create_paste(uuid, paste_content.encode(), ltags, ltagsgalaxies, uuid)
                remove_submit_uuid(uuid)
                time.sleep(0.5)

        # wait for paste
        else:
            publisher.debug("Script submit_paste is Idling 10s")
            time.sleep(3)

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import datetime
import logging.config
import magic
import os
import sys

from werkzeug.utils import secure_filename

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_logger
from lib.ail_core import generate_uuid
# from lib import ConfigLoader
from packages import Date

logging.config.dictConfig(ail_logger.get_config(name='modules'))
logger = logging.getLogger()

# config_loader = ConfigLoader.ConfigLoader()
# r_serv = config_loader.get_db_conn("Kvrocks_Stats")   # TODO CHANGE DB
# r_cache = config_loader.get_redis_conn("Redis_Log_submit")
#
# # Text max size
# TEXT_MAX_SIZE = ConfigLoader.ConfigLoader().get_config_int("SubmitPaste", "TEXT_MAX_SIZE")
# # File max size
# FILE_MAX_SIZE = ConfigLoader.ConfigLoader().get_config_int("SubmitPaste", "FILE_MAX_SIZE")
# # Allowed file type
# ALLOWED_EXTENSIONS = ConfigLoader.ConfigLoader().get_config_str("SubmitPaste", "FILE_ALLOWED_EXTENSIONS").split(',')
# config_loader = None
#
# # TODO generate UUID
#
# # TODO Source ????
#
# # TODO RENAME ME
# class Submit:
#     def __init__(self, submit_uuid):
#         self.uuid = submit_uuid
#
#     def exists(self):
#         return r_serv.exists(f'submit:{self.uuid}')
#
#     def is_item(self):
#         return r_serv.hexists(f'submit:{self.uuid}', 'content')
#
#     def is_file(self):
#         return r_serv.hexists(f'submit:{self.uuid}', 'filename')
#
#     def get_filename(self):
#         return r_serv.hget(f'submit:{self.uuid}', 'filename')
#
#     def get_content(self):
#         return r_serv.hget(f'submit:{self.uuid}', 'content')
#
#     def get_password(self):
#         r_serv.hget(f'submit:{self.uuid}', 'password')
#
#     def get_tags(self):
#         return r_serv.smembers(f'submit:tags:{self.uuid}')
#
#     def get_error(self):
#         return r_cache.hget(f'submit:{self.uuid}:', 'error')
#
#     def get_stats(self):
#         stats = {'ended': r_cache.hget(f'submit:{self.uuid}', 'ended'), # boolean
#                  'objs': r_cache.hget(f'submit:{self.uuid}', 'objs'), # objs IDs
#                  'nb_files': r_cache.hget(f'submit:{self.uuid}', 'nb_files'),
#                  'nb_done': r_cache.hget(f'submit:{self.uuid}', 'nb_done'),
#                  'submitted': r_cache.hget(f'submit:{self.uuid}', 'submitted'),
#                  'error': self.get_error()}
#         return stats
#
#
#     def get_meta(self):
#         meta = {'uuid': self.uuid}
#         return meta
#
#     def is_compressed(self):
#         pass
#
#
#     def abort(self, message):
#         self.set_error(message)
#         r_cache.hset(f'submit:{self.uuid}', 'ended', 'True')
#         self.delete()
#
#     def set_error(self, message):
#
#         r_serv.hset(f'submit:{self.uuid}', 'error', )
#
#     # source ???
#     def create(self, content='', filename='', tags=[], password=None):
#
#
#
#
#         r_serv.sadd(f'submits:all')
#
#
#     def delete(self):
#         r_serv.srem(f'submits:all', self.uuid)
#         r_cache.delete(f'submit:{self.uuid}')
#         r_serv.delete(f'submit:tags:{self.uuid}')
#         r_serv.delete(f'submit:{self.uuid}')
#
#
# def create_submit(tags=[]):
#     submit_uuid = generate_uuid()
#     submit = Submit(submit_uuid)
#
# def api_create_submit():
#     pass


#########################################################################################
#########################################################################################
#########################################################################################

ARCHIVE_MIME_TYPE = {
    'application/zip',
    # application/bzip2
    'application/x-bzip2',
    'application/java-archive',
    'application/x-tar',
    'application/gzip',
    # application/x-gzip
    'application/x-lzma',
    'application/x-xz',
    # application/x-xz-compressed-tar
    'application/x-lz',
    'application/x-7z-compressed',
    'application/x-rar',
    # application/x-rar-compressed
    'application/x-iso9660-image',
    'application/vnd.ms-cab-compressed',
    # application/x-lzma
    # application/x-compress
    # application/x-lzip
    # application/x-lz4
    # application/zstd
}

def is_archive(mimetype):
    return mimetype in ARCHIVE_MIME_TYPE

def is_text(mimetype):
    return mimetype.split('/')[0] == 'text'


def get_mimetype(b_content):
    return magic.from_buffer(b_content, mime=True)

def create_item_id(feeder_name, path):
    names = path.split('/')
    try:
        date = datetime.datetime(int(names[-4]), int(names[-3]), int(names[-2])).strftime("%Y%m%d")
        basename = names[-1]
    except (IndexError, ValueError):
        date = Date.get_today_date_str()
        basename = path  # TODO check max depth
    date = f'{date[0:4]}/{date[4:6]}/{date[6:8]}'
    basename = secure_filename(basename)
    if len(basename) < 1:
        basename = generate_uuid()
    if len(basename) > 215:
        basename = basename[-215:] + str(generate_uuid())
    if not basename.endswith('.gz'):
        basename = basename.replace('.', '_')
        basename = f'{basename}.gz'
    else:
        nb = basename.count('.') - 1
        if nb > 0:
            basename = basename.replace('.', '_', nb)
    item_id = os.path.join(feeder_name, date, basename)
    # TODO check if already exists
    return item_id

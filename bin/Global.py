#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The ZMQ_Feed_Q Module
=====================

This module is consuming the Redis-list created by the ZMQ_Feed_Q Module,
And save the paste on disk to allow others modules to work on them.

..todo:: Be able to choose to delete or not the saved paste after processing.
..todo:: Store the empty paste (unprocessed) somewhere in Redis.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances.
*Need the ZMQ_Feed_Q Module running to be able to work properly.

"""

##################################
# Import External packages
##################################
import base64
import hashlib
import io
import gzip
import os
import sys
import time
import uuid
import datetime
import redis
from pubsublogger import publisher


##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader
from Helper import Process


class Global(AbstractModule):
    """
    Global module for AIL framework
    """
    
    def __init__(self):
        super(Global, self).__init__()

        self.r_stats = ConfigLoader.ConfigLoader().get_redis_conn("ARDB_Statistics")
        
        self.processed_paste = 0
        #  TODO rename time_1 explicitely
        self.time_1 = time.time()

        # Get and sanityze PASTE DIRECTORY
        self.PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], self.process.config.get("Directories", "pastes"))
        self.PASTES_FOLDERS = self.PASTES_FOLDER + '/'
        self.PASTES_FOLDERS = os.path.join(os.path.realpath(self.PASTES_FOLDERS), '')

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 0.5

        # Send module state to logs
        self.redis_logger.info(f"Module {self.module_name} initialized")


    def computeNone(self):
        difftime = time.time() - self.time_1
        if int(difftime) > 30:
            to_print = f'Global; ; ; ;glob Processed {self.processed_paste} paste(s) in {difftime} s'
            self.redis_logger.debug(to_print)

            self.time_1 = time.time()
            self.processed_paste = 0


    def compute(self, message):
        # Recovering the streamed message informations
        splitted = message.split()

        if len(splitted) == 2:
            paste, gzip64encoded = splitted

            # Remove PASTES_FOLDER from item path (crawled item + submited)
            if self.PASTES_FOLDERS in paste:
                paste = paste.replace(self.PASTES_FOLDERS, '', 1)

            file_name_paste = paste.split('/')[-1]
            if len(file_name_paste) > 255:
                new_file_name_paste = '{}{}.gz'.format(file_name_paste[:215], str(uuid.uuid4()))
                paste = self.rreplace(paste, file_name_paste, new_file_name_paste, 1)

            # Creating the full filepath
            filename = os.path.join(self.PASTES_FOLDER, paste)
            filename = os.path.realpath(filename)

            # Incorrect filename
            if not os.path.commonprefix([filename, self.PASTES_FOLDER]) == self.PASTES_FOLDER:
                self.redis_logger.warning(f'Global; Path traversal detected {filename}')
            
            else:
                # Decode compressed base64
                decoded = base64.standard_b64decode(gzip64encoded)
                new_file_content = self.gunzip_bytes_obj(decoded)

                if new_file_content:

                    filename = self.check_filename(filename, new_file_content)

                    if filename:

                        # create subdir
                        dirname = os.path.dirname(filename)
                        if not os.path.exists(dirname):
                            os.makedirs(dirname)

                        with open(filename, 'wb') as f:
                            f.write(decoded)

                        paste = filename
                        # remove self.PASTES_FOLDER from
                        if self.PASTES_FOLDERS in paste:
                            paste = paste.replace(self.PASTES_FOLDERS, '', 1)

                        self.process.populate_set_out(paste)
                        self.processed_paste+=1

        else:
            # TODO Store the name of the empty paste inside a Redis-list
            self.redis_logger.debug(f"Empty Paste: {message} not processed")


    def check_filename(self, filename, new_file_content):
        """
        Check if file is not a duplicated file
        return the filename if new file, else None
        """

        # check if file exist
        if os.path.isfile(filename):
            self.redis_logger.warning(f'File already exist {filename}')

            # Check that file already exists but content differs
            curr_file_content = self.gunzip_file(filename)

            if curr_file_content:
                # Compare file content with message content with MD5 checksums
                curr_file_md5 = hashlib.md5(curr_file_content).hexdigest()
                new_file_md5 = hashlib.md5(new_file_content).hexdigest()

                if new_file_md5 != curr_file_md5:
                    # MD5 are not equals, verify filename
                    if filename.endswith('.gz'):
                        filename = f'{filename[:-3]}_{new_file_md5}.gz'
                    else:
                        filename = f'{filename}_{new_file_md5}'

                    self.redis_logger.debug(f'new file to check: {filename}')

                    if os.path.isfile(filename):
                        # Ignore duplicate
                        self.redis_logger.debug(f'ignore duplicated file {filename}')
                        filename = None

                else:
                    # Ignore duplicate checksum equals
                    self.redis_logger.debug(f'ignore duplicated file {filename}')
                    filename = None
            
            else:
                # File not unzipped
                filename = None
                
        
        return filename


    def gunzip_file(self, filename):
        """
        Unzip a file
        publish stats if failure
        """
        curr_file_content = None

        try:
            with gzip.open(filename, 'rb') as f:
                curr_file_content = f.read()
        except EOFError:
            self.redis_logger.warning(f'Global; Incomplete file: {filename}')
            # save daily stats
            self.r_stats.zincrby('module:Global:incomplete_file', datetime.datetime.now().strftime('%Y%m%d'), 1)
        except OSError:
            self.redis_logger.warning(f'Global; Not a gzipped file: {filename}')
            # save daily stats
            self.r_stats.zincrby('module:Global:invalid_file', datetime.datetime.now().strftime('%Y%m%d'), 1)

        return curr_file_content


    def gunzip_bytes_obj(self, bytes_obj):
        gunzipped_bytes_obj = None

        try:
            in_ = io.BytesIO()
            in_.write(bytes_obj)
            in_.seek(0)
            
            with gzip.GzipFile(fileobj=in_, mode='rb') as fo:
                gunzipped_bytes_obj = fo.read()

        except Exception as e:
            self.redis_logger.warning(f'Global; Invalid Gzip file: {filename}, {e}')

        return gunzipped_bytes_obj


    def rreplace(self, s, old, new, occurrence):
        li = s.rsplit(old, occurrence)

        return new.join(li)


if __name__ == '__main__':
    
    module = Global()
    module.run()

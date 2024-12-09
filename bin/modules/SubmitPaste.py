#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Submit paste module
================

"""

##################################
# Import External packages
##################################
import os
import sys
import gzip
import base64
import datetime
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Items import ITEMS_FOLDER
from lib import ConfigLoader
from lib import Tag
from lib.objects.Items import Item

class SubmitPaste(AbstractModule):
    """
    SubmitPaste module for AIL framework
    """

    expire_time = 120
    # Text max size
    TEXT_MAX_SIZE = ConfigLoader.ConfigLoader().get_config_int("SubmitPaste", "TEXT_MAX_SIZE")
    # File max size
    FILE_MAX_SIZE = ConfigLoader.ConfigLoader().get_config_int("SubmitPaste", "FILE_MAX_SIZE")
    # Allowed file type
    ALLOWED_EXTENSIONS = ConfigLoader.ConfigLoader().get_config_str("SubmitPaste", "FILE_ALLOWED_EXTENSIONS").split(',')

    def __init__(self):
        """
        init
        """
        super(SubmitPaste, self).__init__()

        self.r_serv_db = ConfigLoader.ConfigLoader().get_db_conn("Kvrocks_DB")
        self.r_serv_log_submit = ConfigLoader.ConfigLoader().get_redis_conn("Redis_Log_submit")

        self.pending_seconds = 3

        self.PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], ConfigLoader.ConfigLoader().get_config_str("Directories", "pastes")) + '/'

    def compute(self, uuid):
        """
        Main method of the Module to implement
        """
        self.logger.debug(f'compute UUID {uuid}')

        # get temp value save on disk
        ltags = self.r_serv_db.smembers(f'{uuid}:ltags')
        ltagsgalaxies = self.r_serv_db.smembers(f'{uuid}:ltagsgalaxies')
        paste_content = self.r_serv_db.get(f'{uuid}:paste_content')
        isfile = self.r_serv_db.get(f'{uuid}:isfile')
        password = self.r_serv_db.get(f'{uuid}:password')
        source = self.r_serv_db.get(f'{uuid}:source')

        if source in ['crawled', 'tests']:
            source = 'submitted'

        self.logger.debug(f'isfile UUID {isfile}')
        self.logger.debug(f'source UUID {source}')
        self.logger.debug(f'paste_content UUID {paste_content}')

        # needed if redis is restarted
        self.r_serv_log_submit.set(f'{uuid}:end', 0)
        self.r_serv_log_submit.set(f'{uuid}:processing', 0)
        self.r_serv_log_submit.set(f'{uuid}:nb_total', -1)
        self.r_serv_log_submit.set(f'{uuid}:nb_end', 0)
        self.r_serv_log_submit.set(f'{uuid}:nb_sucess', 0)

        self.r_serv_log_submit.set(f'{uuid}:processing', 1)

        if isfile == 'True':
            #  file input
            self._manage_file(uuid, paste_content, ltags, ltagsgalaxies, source)

        else:
            # textarea input paste
            self._manage_text(uuid, paste_content, ltags, ltagsgalaxies, source)

        # new paste created from file, remove uuid ref
        self.remove_submit_uuid(uuid)


    def run(self):
        """
        Run Module endless process
        """

        # Endless loop processing messages from the input queue
        while self.proceed:
            # Get one message (paste) from the QueueIn (copy of Redis_Global publish)
            nb_submit = self.r_serv_db.scard('submitted:uuid')

            if nb_submit > 0:
                try:
                    uuid = self.r_serv_db.srandmember('submitted:uuid')
                    if isinstance(uuid, list):
                        uuid = uuid[0]
                    # Module processing with the message from the queue
                    self.logger.debug(uuid)
                    self.compute(uuid)
                except Exception as err:
                    self.logger.critical(err)
                    # Remove uuid ref
                    self.remove_submit_uuid(uuid)
            else:
                # Wait before next process
                self.logger.debug(f'{self.module_name}, waiting for new message, Idling {self.pending_seconds}s')
                time.sleep(self.pending_seconds)

    def _manage_text(self, uuid, paste_content, ltags, ltagsgalaxies, source):
        """
        Create a paste for given text
        """
        if sys.getsizeof(paste_content) < SubmitPaste.TEXT_MAX_SIZE:
            self.r_serv_log_submit.set(f'{uuid}:nb_total', 1)
            self.create_paste(uuid, paste_content.encode(), ltags, ltagsgalaxies, uuid, source)
            time.sleep(0.5)
        else:
            self.abord_file_submission(uuid, f'Text size is over {SubmitPaste.TEXT_MAX_SIZE} bytes')

    def _manage_file(self, uuid, file_full_path, ltags, ltagsgalaxies, source):
        """
        Create a paste for given file
        """

        if os.path.exists(file_full_path):
            self.logger.debug(f'file exists {file_full_path}')

            file_size = os.stat(file_full_path).st_size
            self.logger.debug(f'file size {file_size}')
            # Verify file length
            if file_size < SubmitPaste.FILE_MAX_SIZE:
                # TODO sanitize filename
                filename = file_full_path.split('/')[-1]
                self.logger.debug(f'sanitize filename {filename}')
                self.logger.debug('file size allowed')

                if not '.' in filename:
                    self.logger.debug('no extension for filename')
                    try:
                        # Read file
                        with open(file_full_path,'r') as f:
                            content = f.read()
                            self.r_serv_log_submit.set(uuid + ':nb_total', 1)
                            self.create_paste(uuid, content.encode(), ltags, ltagsgalaxies, uuid, source)
                    except:
                        self.abord_file_submission(uuid, "file error")

                else:
                    file_type = filename.rsplit('.', 1)[1]
                    file_type = file_type.lower()
                    self.logger.debug(f'file ext {file_type}')

                    if file_type in SubmitPaste.ALLOWED_EXTENSIONS:
                        self.logger.debug('Extension allowed')
                        # TODO enum of possible file extension ?
                        # TODO verify file hash with virus total ?
                        if not self._is_compressed_type(file_type):
                            self.logger.debug('Plain text file')
                            # plain txt file
                            with open(file_full_path,'r') as f:
                                content = f.read()
                                self.r_serv_log_submit.set(uuid + ':nb_total', 1)
                                self.create_paste(uuid, content.encode(), ltags, ltagsgalaxies, uuid, source)
                        else:
                        # Compressed file
                            self.abord_file_submission(uuid, "file decompression should be implemented")
                            # TODO add compress file management
                            # #decompress file
                            # try:
                            #     if password == None:
                            #         files = unpack(file_full_path.encode())
                            #         #print(files.children)
                            #     else:
                            #         try:
                            #             files = unpack(file_full_path.encode(), password=password.encode())
                            #             #print(files.children)
                            #         except sflock.exception.IncorrectUsageException:
                            #             self.abord_file_submission(uuid, "Wrong Password")
                            #             raise
                            #         except:
                            #             self.abord_file_submission(uuid, "file decompression error")
                            #             raise
                            #     self.logger.debug('unpacking {} file'.format(files.unpacker))
                            #     if(not files.children):
                            #         self.abord_file_submission(uuid, "Empty compressed file")
                            #         raise
                            #     # set number of files to submit
                            #     self.r_serv_log_submit.set(uuid + ':nb_total', len(files.children))
                            #     n = 1
                            #     for child in files.children:
                            #         if self.verify_extention_filename(child.filename.decode()):
                            #             self.create_paste(uuid, child.contents, ltags, ltagsgalaxies, uuid+'_'+ str(n) , source)
                            #             n = n + 1
                            #         else:
                            #             self.logger.error("Error in module %s: bad extention"%(self.module_name))
                            #             self.addError(uuid, 'Bad file extension: {}'.format(child.filename.decode()) )

                            # except FileNotFoundError:
                            #     self.logger.error("Error in module %s: file not found"%(self.module_name))
                            #     self.addError(uuid, 'File not found: {}'.format(file_full_path), uuid )

            else:
                self.abord_file_submission(uuid, f'File :{file_full_path} too large, over {SubmitPaste.FILE_MAX_SIZE} bytes')
        else:
            self.abord_file_submission(uuid, "Server Error, the archive can't be found")

    def _is_compressed_type(self, file_type):
        """
        Check if file type is in the list of compressed file extensions format
        """
        compressed_type = ['zip', 'gz', 'tar.gz']

        return file_type in compressed_type

    def remove_submit_uuid(self, uuid):
        # save temp value on disk
        self.r_serv_db.delete(f'{uuid}:ltags')
        self.r_serv_db.delete(f'{uuid}:ltagsgalaxies')
        self.r_serv_db.delete(f'{uuid}:paste_content')
        self.r_serv_db.delete(f'{uuid}:isfile')
        self.r_serv_db.delete(f'{uuid}:password')
        self.r_serv_db.delete(f'{uuid}:source')

        self.r_serv_log_submit.expire(f'{uuid}:end', SubmitPaste.expire_time)
        self.r_serv_log_submit.expire(f'{uuid}:processing', SubmitPaste.expire_time)
        self.r_serv_log_submit.expire(f'{uuid}:nb_total', SubmitPaste.expire_time)
        self.r_serv_log_submit.expire(f'{uuid}:nb_sucess', SubmitPaste.expire_time)
        self.r_serv_log_submit.expire(f'{uuid}:nb_end', SubmitPaste.expire_time)
        self.r_serv_log_submit.expire(f'{uuid}:error', SubmitPaste.expire_time)
        self.r_serv_log_submit.expire(f'{uuid}:paste_submit_link', SubmitPaste.expire_time)

        # delete uuid
        self.r_serv_db.srem('submitted:uuid', uuid)
        self.logger.debug(f'{uuid} all file submitted')
        print(f'{uuid} all file submitted')

    def create_paste(self, uuid, paste_content, ltags, ltagsgalaxies, name, source=None):
        # # TODO: Use Item create

        result = False

        now = datetime.datetime.now()
        source = source if source else 'submitted'
        save_path = source + '/' + now.strftime("%Y") + '/' + now.strftime("%m") + '/' + now.strftime("%d") + '/submitted_' + name + '.gz'

        full_path = os.path.join(ITEMS_FOLDER, save_path)

        self.logger.debug(f'file path of the paste {full_path}')

        if not os.path.isfile(full_path):
            # file not exists in AIL paste directory
            self.logger.debug(f"new paste {paste_content}")

            gzip64encoded = self._compress_encode_content(paste_content, uuid)

            if gzip64encoded:

                # use relative path
                rel_item_path = save_path.replace(self.PASTES_FOLDER, '', 1)
                self.logger.debug(f"relative path {rel_item_path}")

                item = Item(rel_item_path)

                # send paste to Global module
                relay_message = f"submitted {gzip64encoded}"
                self.add_message_to_queue(obj=item, message=relay_message)

                # add tags
                for tag in ltags:
                    Tag.add_object_tag(tag, 'item', rel_item_path)

                for tag in ltagsgalaxies:
                    Tag.add_object_tag(tag, 'item', rel_item_path)

                self.r_serv_log_submit.incr(f'{uuid}:nb_end')
                self.r_serv_log_submit.incr(f'{uuid}:nb_sucess')

                if self.r_serv_log_submit.get(f'{uuid}:nb_end') == self.r_serv_log_submit.get(f'{uuid}:nb_total'):
                    self.r_serv_log_submit.set(f'{uuid}:end', 1)

                self.logger.debug(f'    {rel_item_path} send to Mixer')
                print(f'    {rel_item_path} send to Mixer')
                self.r_serv_log_submit.sadd(f'{uuid}:paste_submit_link', rel_item_path)

                curr_date = datetime.date.today()
                self.logger.debug("paste submitted")
        else:
            self.addError(uuid, f'File: {save_path} already exist in submitted pastes')

        return result

    def _compress_encode_content(self, content, uuid):
        gzip64encoded = None
        try:
            gzipencoded = gzip.compress(content)
            gzip64encoded = base64.standard_b64encode(gzipencoded).decode()
        except:
            self.abord_file_submission(uuid, "file error")
        return gzip64encoded

    def addError(self, uuid, errorMessage):
        self.logger.debug(errorMessage)
        print(errorMessage)
        error = self.r_serv_log_submit.get(f'{uuid}:error')
        if error is not None:
            self.r_serv_log_submit.set(f'{uuid}:error', error + '<br></br>' + errorMessage)
        self.r_serv_log_submit.incr(f'{uuid}:nb_end')

    def abord_file_submission(self, uuid, errorMessage):
        self.logger.debug(f'abord {uuid}, {errorMessage}')

        self.addError(uuid, errorMessage)
        self.r_serv_log_submit.set(f'{uuid}:end', 1)
        curr_date = datetime.date.today()
        self.remove_submit_uuid(uuid)

    # # TODO: use Item function
    def get_item_date(self, item_filename):
        l_directory = item_filename.split('/')
        return f'{l_directory[-4]}{l_directory[-3]}{l_directory[-2]}'

    def verify_extention_filename(self, filename):
        if not '.' in filename:
            return True
        else:
            file_type = filename.rsplit('.', 1)[1]

            # txt file
            if file_type in SubmitPaste.ALLOWED_EXTENSIONS:
                return True
            else:
                return False


if __name__ == '__main__':
    module = SubmitPaste()
    module.run()

# coding: utf-8
"""
Base Class for AIL Modules
"""

##################################
# Import External packages
##################################
from abc import ABC, abstractmethod
import os
import logging
import logging.config
import sys
import time
import traceback

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_logger
from lib.ail_queues import AILQueue
from lib import regex_helper
from lib.exceptions import ModuleQueueError, TimeoutException
from lib.objects.ail_objects import get_obj_from_global_id

logging.config.dictConfig(ail_logger.get_config(name='modules'))

class AbstractModule(ABC):
    """
    Abstract Module class
    """

    def __init__(self, module_name=None, queue=True):
        """
        AIL Module,
        module_name: str; set the module name if different from the instance ClassName
        :param queue: Allow to push messages to other modules
        """
        self.logger = logging.getLogger(f'{self.__class__.__name__}')

        # Module name if provided else instance className
        self.module_name = module_name if module_name else self._module_name()

        self.pid = os.getpid()

        # Setup the I/O queues
        if queue:
            self.queue = AILQueue(self.module_name, self.pid)
            self.obj = None
            self.sha256_mess = None

        # Cache key
        self.r_cache_key = regex_helper.generate_redis_cache_key(self.module_name)
        self.max_execution_time = 30

        # Run module endlessly
        self.proceed = True

        # Waiting time in seconds between two processed messages
        self.pending_seconds = 10

        # Debug Mode
        self.debug = False

        if queue:
            self.queue.start()

    def get_obj(self):
        return self.obj

    def set_obj(self, new_obj):
        if self.obj:
            old_id = self.obj.id
            self.obj = new_obj
            self.queue.rename_message_obj(self.obj.id, old_id)
        else:
            self.obj = new_obj

    def get_message(self):
        """
        Get message from the Redis Queue (QueueIn)
        Input message can change between modules
        ex: '<item id>'
        """
        message = self.queue.get_message()
        if message:
            obj_global_id, sha256_mess, mess = message
            if obj_global_id:
                self.sha256_mess = sha256_mess
                self.obj = get_obj_from_global_id(obj_global_id)
            else:
                self.sha256_mess = None
                self.obj = None
            return mess
        self.sha256_mess = None
        self.obj = None
        return None

    # TODO ADD META OBJ ????
    def add_message_to_queue(self, obj=None, message='', queue=None):
        """
        Add message to queue
        :param obj: AILObject
        :param message: message to send in queue
        :param queue: queue name or module name

        ex: add_message_to_queue(item_id, 'Mail')
        """
        if obj:
            obj_global_id = obj.get_global_id()
        elif self.obj:
            obj_global_id = self.obj.get_global_id()
        else:
            obj_global_id = '::'
        self.queue.send_message(obj_global_id, message, queue)

    def get_available_queues(self):
        return self.queue.get_out_queues()

    def regex_match(self, regex, obj_id, content):
        return regex_helper.regex_match(self.r_cache_key, regex, obj_id, content, max_time=self.max_execution_time)

    def regex_search(self, regex, obj_id, content):
        return regex_helper.regex_search(self.r_cache_key, regex, obj_id, content, max_time=self.max_execution_time)

    def regex_finditer(self, regex, obj_id, content):
        return regex_helper.regex_finditer(self.r_cache_key, regex, obj_id, content, max_time=self.max_execution_time)

    def regex_findall(self, regex, obj_id, content, r_set=False):
        """
        regex findall helper (force timeout)
        :param regex: compiled regex
        :param obj_id: object id
        :param content: object content
        :param r_set: return result as set
        """
        return regex_helper.regex_findall(self.module_name, self.r_cache_key, regex, obj_id, content,
                                          max_time=self.max_execution_time, r_set=r_set)

    def regex_phone_iter(self, country_code, obj_id, content):
        """
        regex findall helper (force timeout)
        :param regex: compiled regex
        :param obj_id: object id
        :param content: object content
        :param r_set: return result as set
        """
        return regex_helper.regex_phone_iter(self.r_cache_key, country_code, obj_id, content,
                                             max_time=self.max_execution_time)

    def run(self):
        """
        Run Module endless process
        """

        # Endless loop processing messages from the input queue
        while self.proceed:
            # Get one message (ex:item id) from the Redis Queue (QueueIn)
            message = self.get_message()

            if message or self.obj:
                try:
                    # Module processing with the message from the queue
                    self.compute(message)
                except Exception as err:
                    if self.debug:
                        self.queue.error()
                        raise err

                    # LOG ERROR
                    trace = traceback.format_tb(err.__traceback__)
                    trace = ''.join(trace)
                    self.logger.critical(f"Error in module {self.module_name}: {__name__} : {err}")
                    if message:
                        self.logger.critical(f"Module {self.module_name} input message: {message}")
                    if self.obj:
                        self.logger.critical(f"{self.module_name} Obj: {self.obj.get_global_id()}")
                    self.logger.critical(trace)

                    if isinstance(err, ModuleQueueError):
                        self.queue.error()
                        raise err
                # remove from set_module
                ## check if item process == completed

                if self.obj:
                    self.queue.end_message(self.obj.get_global_id(), self.sha256_mess)
                    self.obj = None
                    self.sha256_mess = None

            else:
                self.computeNone()
                # Wait before next process
                self.logger.debug(f"{self.module_name}, waiting for new message, Idling {self.pending_seconds}s")
                try:
                    time.sleep(self.pending_seconds)
                except TimeoutException:
                    pass

    def _module_name(self):
        """
        Returns the instance class name (ie the Module Name)
        """
        return self.__class__.__name__

    @abstractmethod
    def compute(self, message):
        """
        Main method of the Module to implement
        """
        pass

    def compute_manual(self, obj, message=None):
        self.obj = obj
        return self.compute(message)

    def computeNone(self):
        """
        Method of the Module when there is no message
        """
        pass

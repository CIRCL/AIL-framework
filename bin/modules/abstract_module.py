# coding: utf-8
"""
Base Class for AIL Modules
"""

##################################
# Import External packages
##################################
from abc import ABC, abstractmethod
import os
import sys
import time
import traceback

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from pubsublogger import publisher
from lib.ail_queues import AILQueue
from lib import regex_helper
from lib.exceptions import ModuleQueueError

class AbstractModule(ABC):
    """
    Abstract Module class
    """

    def __init__(self, module_name=None, logger_channel='Script', queue=True):
        """
        Init Module
        module_name: str; set the module name if different from the instance ClassName
        queue_name: str; set the queue name if different from the instance ClassName
        logger_channel: str; set the logger channel name, 'Script' by default
        """
        # Module name if provided else instance className
        self.module_name = module_name if module_name else self._module_name()

        self.pid = os.getpid()

        # Setup the I/O queues
        if queue:
            self.queue = AILQueue(self.module_name, self.pid)

        # Init Redis Logger
        self.redis_logger = publisher

        # Port of the redis instance used by pubsublogger
        self.redis_logger.port = 6380

        # Channel name to publish logs
        # # TODO: refactor logging
        # If provided could be a namespaced channel like script:<ModuleName>
        self.redis_logger.channel = logger_channel

        # Cache key
        self.r_cache_key = regex_helper.generate_redis_cache_key(self.module_name)
        self.max_execution_time = 30

        # Run module endlessly
        self.proceed = True

        # Waiting time in seconds between two processed messages
        self.pending_seconds = 10

        # Debug Mode
        self.debug = False

    def get_message(self):
        """
        Get message from the Redis Queue (QueueIn)
        Input message can change between modules
        ex: '<item id>'
        """
        return self.queue.get_message()

    def add_message_to_queue(self, message, queue_name=None):
        """
        Add message to queue
        :param message: message to send in queue
        :param queue_name: queue or module name

        ex: add_message_to_queue(item_id, 'Mail')
        """
        self.queue.send_message(message, queue_name)
        # add to new set_module

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

    def run(self):
        """
        Run Module endless process
        """

        # Endless loop processing messages from the input queue
        while self.proceed:
            # Get one message (ex:item id) from the Redis Queue (QueueIn)
            message = self.get_message()

            if message:
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
                    self.redis_logger.critical(f"Error in module {self.module_name}: {err}")
                    self.redis_logger.critical(f"Module {self.module_name} input message: {message}")
                    self.redis_logger.critical(trace)
                    print()
                    print(f"ERROR: {err}")
                    print(f'MESSAGE: {message}')
                    print('TRACEBACK:')
                    print(trace)

                    if isinstance(err, ModuleQueueError):
                        self.queue.error()
                        raise err
                # remove from set_module
                ## check if item process == completed

            else:
                self.computeNone()
                # Wait before next process
                self.redis_logger.debug(f"{self.module_name}, waiting for new message, Idling {self.pending_seconds}s")
                time.sleep(self.pending_seconds)

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

    def computeNone(self):
        """
        Method of the Module when there is no message
        """
        pass

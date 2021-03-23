# coding: utf-8
"""
Base Class for AIL Modules
"""

##################################
# Import External packages
##################################
from abc import ABC, abstractmethod
from builtins import classmethod
import logging
from logging.handlers import TimedRotatingFileHandler
import time

##################################
# Import Project packages
##################################
from pubsublogger import publisher
from Helper import Process


class AbstractModule(ABC):
    """
    Abstract Module class
    """

    def __init__(self, module_name=None, queue_name=None):
        """
        Init Module
        module_name: str; set the module name if different from the instance ClassName
        """
        # Module name if provided else instance className
        self.module_name = module_name if module_name else self._module_name()

        # Module name if provided else instance className
        self.queue_name = queue_name if queue_name else self._module_name()

        # Init Redis Logger
        self.redis_logger = publisher
        # Port of the redis instance used by pubsublogger
        self.redis_logger.port = 6380
        # Channel name to publish logs
        self.redis_logger.channel = 'Script'
        # TODO modify generic channel Script to a namespaced channel like:
        # publish module logs to script:<ModuleName> channel
        # self.redis_logger.channel = 'script:%s'%(self.module_name)

        # Run module endlessly
        self.proceed = True

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 10

        # Setup the I/O queues
        self.process = Process(self.queue_name)


    def run(self):
        """
        Run Module endless process
        """
        
        # Endless loop processing messages from the input queue
        while self.proceed:
            # Get one message (paste) from the QueueIn (copy of Redis_Global publish)
            message = self.process.get_from_set()
            
            if message is None:
                self.computeNone()
                # Wait before next process
                self.redis_logger.debug('%s, waiting for new message, Idling %ds'%(self.module_name, self.pending_seconds))
                # self.file_logger.debug('%s, waiting for new message'%(self.module_name)
                time.sleep(self.pending_seconds)
                continue

            try:
                # Module processing with the message from the queue
                self.compute(message)
            except Exception as err:
                self.redis_logger.error("Error in module %s: %s"%(self.module_name, err))
                self.file_logger.error("Error in module %s: %s"%(self.module_name, err))


    def _module_name(self):
        """
        Returns the instance class name (ie. the Module Name)
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

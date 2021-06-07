# coding: utf-8
"""
Base Class for AIL Modules
"""

##################################
# Import External packages
##################################
from abc import ABC, abstractmethod
import time
import traceback

##################################
# Import Project packages
##################################
from pubsublogger import publisher
from Helper import Process

class AbstractModule(ABC):
    """
    Abstract Module class
    """

    def __init__(self, module_name=None, queue_name=None, logger_channel='Script'):
        """
        Init Module
        module_name: str; set the module name if different from the instance ClassName
        queue_name: str; set the queue name if different from the instance ClassName
        logger_channel: str; set the logger channel name, 'Script' by default
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
        # # TODO: refactor logging
        # If provided could be a namespaced channel like script:<ModuleName>
        self.redis_logger.channel = logger_channel


        # Run module endlessly
        self.proceed = True

        # Waiting time in secondes between two proccessed messages
        self.pending_seconds = 10

        # Setup the I/O queues
        self.process = Process(self.queue_name)

    def get_message(self):
        """
        Get message from the Redis Queue (QueueIn)
        Input message can change between modules
        ex: '<item id>'
        """
        return self.process.get_from_set()

    def send_message_to_queue(self, message, queue_name=None):
        """
        Send message to queue
        :param message: message to send in queue
        :param queue_name: queue or module name

        ex: send_to_queue(item_id, 'Global')
        """
        self.process.populate_set_out(message, queue_name)

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
                    trace = traceback.format_tb(err.__traceback__)
                    self.redis_logger.critical(f"Error in module {self.module_name}: {err}")
                    self.redis_logger.critical(trace)
                    print()
                    print(f"ERROR: {err}")
                    print(f'MESSAGE: {message}')
                    print('TRACEBACK:')
                    for line in trace:
                        print(line)

            else:
                self.computeNone()
                # Wait before next process
                self.redis_logger.debug(f"{self.module_name}, waiting for new message, Idling {self.pending_seconds}s")
                time.sleep(self.pending_seconds)


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

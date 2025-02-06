#!/usr/bin/env python3
# -*-coding:UTF-8 -*

# from pymisp import PyMISPError

# SIGNAL ALARM
class TimeoutException(Exception):
    pass

class AILError(Exception):
    def __init__(self, message):
        super(AILError, self).__init__(message)
        self.message = message

class UpdateInvestigationError(AILError):
    pass

class NewTagError(AILError):
    pass

class ModuleQueueError(AILError):
    pass

class MISPConnectionError(AILError):
    pass

class AILObjectUnknown(AILError):
    pass

class OnionFilteringError(AILError):
    pass

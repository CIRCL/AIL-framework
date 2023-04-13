#!/usr/bin/env python3
# -*-coding:UTF-8 -*

class AIL_ERROR(Exception):
    """docstring for AIL_ERROR."""

    def __init__(self, message):
        super(AIL_ERROR, self).__init__(message)
        self.message = message

class UpdateInvestigationError(AIL_ERROR):
    pass

class NewTagError(AIL_ERROR):
    pass

class ModuleQueueError(AIL_ERROR):
    pass

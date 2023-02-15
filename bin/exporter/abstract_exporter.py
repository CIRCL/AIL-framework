#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import os
import sys

from abc import ABC, abstractmethod


# sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
# from ConfigLoader import ConfigLoader

class AbstractExporter(ABC):
    def __init__(self):
        """
        Init Module
        """
        # Module name if provided else instance className
        self.name = self._name()

    def _name(self):
        """
        Returns the instance class name (ie. the Exporter Name)
        """
        return self.__class__.__name__

    @abstractmethod
    def export(self, *args, **kwargs):
        """Importer function"""
        pass
    #     res = self.export(*args, **kwargs)
    #     if self.next_exporter:
    #         self.next_exporter.exporter(res)



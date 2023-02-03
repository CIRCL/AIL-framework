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

class AbstractImporter(ABC):
    def __init__(self):
        """
        Init Module
        importer_name: str; set the importer name if different from the instance ClassName
        """
        # Module name if provided else instance className
        self.name = self._name()

    @abstractmethod
    def importer(self, *args, **kwargs):
        """Importer function"""
        pass

    def _name(self):
        """
        Returns the instance class name (ie. the Exporter Name)
        """
        return self.__class__.__name__



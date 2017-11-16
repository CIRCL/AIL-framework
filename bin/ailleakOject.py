#!/usr/bin/env python3
# -*-coding:UTF-8 -*

from pymisp.tools import GenericObjectGenerator
from packages import Paste

class AilleakObject(AbstractMISPObjectGenerator):
    def __init__(self, moduleName, path):
        super(GenericObject, self).__init__('ail-leak')
        self.moduleName = moduleName
        self.path = path
        self.paste = Paste.Paste(path)
        self.generate_attributes()

    def generate_attributes(self):
        self.add_attribute('type', value=self.moduleName)
        self.add_attribute('origin', value=self.paste.p_source)
        self.add_attribute('last-seen', value=self.paste.p_date)
        self.add_attribute('raw-data', value=self.paste.get_p_content())
        '''
        # duplicated
        duplicate_list = json.loads(paste._get_p_duplicate())
        is_duplicate = True if len(duplicate_list) > 0 else False
        self.add_attribute('duplicate', value=is_duplicate)
        '''

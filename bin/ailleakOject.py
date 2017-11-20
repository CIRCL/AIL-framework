#!/usr/bin/env python3.5
# -*-coding:UTF-8 -*

from pymisp.tools.abstractgenerator import AbstractMISPObjectGenerator
from packages import Paste

class AilleakObject(AbstractMISPObjectGenerator):
    def __init__(self, moduleName, path):
        super(AbstractMISPObjectGenerator, self).__init__('ail-leak')
        self.moduleName = moduleName
        self.path = path
        self.paste = Paste.Paste(path)
        self.generate_attributes()

    def generate_attributes(self):
        self.add_attribute('type', value=self.moduleName)
        self.add_attribute('origin', value=self.paste.p_source)
        self.add_attribute('last-seen', value=self.paste.p_date)
        #self.add_attribute('raw-data', value=self.paste.get_p_content())
        '''
        # duplicated
        duplicate_list = json.loads(paste._get_p_duplicate())
        is_duplicate = True if len(duplicate_list) > 0 else False
        self.add_attribute('duplicate', value=is_duplicate)
        '''


if __name__ == "__main__":

    import sys
    sys.path.append('../')
    from mispKEYS import misp_url, misp_key, misp_verifycert
    from pymisp import PyMISP

    pymisp = PyMISP(misp_url, misp_key, misp_verifycert)

    moduleName = "Credentials"
    path = "/home/sami/git/AIL-framework/PASTES/archive/pastebin.com_pro/2017/08/23/bPFaJymf.gz"

    wrapper = objectWrapper(moduleName, path, pymisp)
    wrapper.pushToMISP()

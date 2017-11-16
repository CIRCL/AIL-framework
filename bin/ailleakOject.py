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
    eventID = "9356"
    mispTYPE = 'ail-leak'

    moduleName = "Credentials"
    path = "/home/sami/git/AIL-framework/PASTES/archive/pastebin.com_pro/2017/08/23/bPFaJymf.gz"

    misp_object = AilleakObject(moduleName, path)
    print('validate mispobj', misp_object._validate())
    print(misp_object)

    # Publish object to MISP
    try:
        templateID = [x['ObjectTemplate']['id'] for x in pymisp.get_object_templates_list() if x['ObjectTemplate']['name'] == mispTYPE][0]
    except IndexError:
        valid_types = ", ".join([x['ObjectTemplate']['name'] for x in pymisp.get_object_templates_list()])
        print ("Template for type %s not found! Valid types are: %s" % (mispTYPE, valid_types))
    print(templateID)
    #r = pymisp.add_object(eventID, templateID, misp_object)

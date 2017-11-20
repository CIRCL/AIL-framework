#!/usr/bin/env python3.5
# -*-coding:UTF-8 -*

from pymisp.tools.abstractgenerator import AbstractMISPObjectGenerator
from packages import Paste
import datetime
import json

class AilleakObject(AbstractMISPObjectGenerator):
    def __init__(self, moduleName, p_source, p_date, p_content, p_duplicate):
        super(AbstractMISPObjectGenerator, self).__init__('ail-leak')
        self.moduleName = moduleName
        self.p_source = p_source
        self.p_date = p_date
        self.p_content = p_content
        self.p_duplicate = p_duplicate
        self.generate_attributes()

    def generate_attributes(self):
        self.add_attribute('type', value=self.moduleName)
        self.add_attribute('origin', value=self.p_source)
        self.add_attribute('last-seen', value=self.p_date)
        self.add_attribute('duplicate-list', value=self.p_duplicate)
        self.add_attribute('raw-data', value=self.p_content)

class ObjectWrapper:
    def __init__(self, pymisp):
        self.pymisp = pymisp
        self.currentID_date = None
        self.eventID_to_push = self.get_daily_event_id()

    def add_new_object(self, moduleName, path):
        self.moduleName = moduleName
        self.path = path
        self.paste = Paste.Paste(path)
        self.p_date = self.date_to_str(self.paste.p_date)
        self.p_source = self.paste.supposed_url
        self.p_content = self.paste.get_p_content().decode('utf8')
        
        temp = self.paste._get_p_duplicate()
        try:
            temp = temp.decode('utf8')
        except AttributeError:
            print('decode error')
        #beautifier
        temp = json.loads(temp)
        to_ret = []
        for dup in temp:
            algo = dup[0]
            path = dup[1].split('/')[-5:]
            perc = dup[2]
            to_ret.append([path, algo, perc])
        self.p_duplicate = str(to_ret)
        

        self.mispObject = AilleakObject(self.moduleName, self.p_source, self.p_date, self.p_content, self.p_duplicate)

        '''
        # duplicated
        duplicate_list = json.loads(paste._get_p_duplicate())
        is_duplicate = True if len(duplicate_list) > 0 else False
        self.add_attribute('duplicate', value=is_duplicate)
        '''


    def date_to_str(self, date):
        return "{0}-{1}-{2}".format(date.year, date.month, date.day)

    def get_all_related_events(self):
        to_search = "Daily AIL-leaks"
        result = self.pymisp.search_all(to_search)
        events = []
        for e in result['response']:
            events.append({'id': e['Event']['id'], 'org_id': e['Event']['org_id'], 'info': e['Event']['info']})
        return events

    def get_daily_event_id(self):
        to_match = "Daily AIL-leaks {}".format(datetime.date.today())
        events = self.get_all_related_events()
        for dic in events:
            info = dic['info']
            e_id = dic['id']
            if info == to_match:
                print('Found: ', info, '->', e_id)
                self.currentID_date = datetime.date.today()
                return e_id
        created_event = self.create_daily_event()['Event']
        new_id = created_event['id']
        print('New event created:', new_id)
        self.currentID_date = datetime.date.today()
        return new_id


    def create_daily_event(self):
        today = datetime.date.today()
        # [0-3]
        distribution = 0
        info = "Daily AIL-leaks {}".format(today)
        # [0-2]
        analysis = 0
        # [1-4]
        threat = 3
        published = False
        org_id = None
        orgc_id = None
        sharing_group_id = None
        date = None
        event = self.pymisp.new_event(distribution, threat, 
                analysis, info, date, 
                published, orgc_id, org_id, sharing_group_id)
        return event

    # Publish object to MISP
    def pushToMISP(self):
        if self.currentID_date != datetime.date.today(): #refresh id
            self.eventID_to_push = self.get_daily_event_id()

        mispTYPE = 'ail-leak'
        try:
            templateID = [x['ObjectTemplate']['id'] for x in self.pymisp.get_object_templates_list() if x['ObjectTemplate']['name'] == mispTYPE][0]
        except IndexError:
            valid_types = ", ".join([x['ObjectTemplate']['name'] for x in self.pymisp.get_object_templates_list()])
            print ("Template for type %s not found! Valid types are: %s" % (mispTYPE, valid_types))
        r = self.pymisp.add_object(self.eventID_to_push, templateID, self.mispObject)
        if 'errors' in r:
            print(r)
        else:
            print('Pushed:', self.moduleName, '->', self.p_source)

'''
if __name__ == "__main__":

    import sys
    sys.path.append('../')
    from mispKEYS import misp_url, misp_key, misp_verifycert
    from pymisp import PyMISP

    pymisp = PyMISP(misp_url, misp_key, misp_verifycert)

    moduleName = "Credentials"
    path = "/home/sami/git/AIL-framework/PASTES/archive/pastebin.com_pro/2017/08/23/bPFaJymf.gz"

    wrapper = ObjectWrapper(moduleName, path, pymisp)
    wrapper.pushToMISP()
'''

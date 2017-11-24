#!/usr/bin/env python3.5
# -*-coding:UTF-8 -*

from pymisp.tools.abstractgenerator import AbstractMISPObjectGenerator
import configparser
from packages import Paste
import datetime
import json
from io import BytesIO

class AilleakObject(AbstractMISPObjectGenerator):
    def __init__(self, moduleName, p_source, p_date, p_content, p_duplicate, p_duplicate_number):
        super(AbstractMISPObjectGenerator, self).__init__('ail-leak')
        self._moduleName = moduleName
        self._p_source = p_source.split('/')[-5:]
        self._p_source = '/'.join(self._p_source)[:-3] # -3 removes .gz
        self._p_date = p_date
        self._p_content = p_content.encode('utf8')
        self._p_duplicate = p_duplicate
        self._p_duplicate_number = p_duplicate_number
        self.generate_attributes()

    def generate_attributes(self):
        self.add_attribute('type', value=self._moduleName)
        self.add_attribute('origin', value=self._p_source, type='text')
        self.add_attribute('last-seen', value=self._p_date)
        if self._p_duplicate_number > 0:
            self.add_attribute('duplicate', value=self._p_duplicate, type='text')
            self.add_attribute('duplicate_number', value=self._p_duplicate_number, type='counter')
        self._pseudofile = BytesIO(self._p_content)
        self.add_attribute('raw-data', value=self._p_source, data=self._pseudofile, type="attachment")

class ObjectWrapper:
    def __init__(self, pymisp):
        self.pymisp = pymisp
        self.currentID_date = None
        self.eventID_to_push = self.get_daily_event_id()
        cfg = configparser.ConfigParser()
        cfg.read('./packages/config.cfg')
        self.maxDuplicateToPushToMISP = cfg.getint("ailleakObject", "maxDuplicateToPushToMISP") 

    def add_new_object(self, moduleName, path):
        self.moduleName = moduleName
        self.path = path
        self.paste = Paste.Paste(path)
        self.p_date = self.date_to_str(self.paste.p_date)
        self.p_source = self.paste.p_path
        self.p_content = self.paste.get_p_content().decode('utf8')
        
        temp = self.paste._get_p_duplicate()
        try:
            temp = temp.decode('utf8')
        except AttributeError:
            pass
        #beautifier
        temp = json.loads(temp)
        self.p_duplicate_number = len(temp) if len(temp) >= 0 else 0
        to_ret = ""
        for dup in temp[:self.maxDuplicateToPushToMISP]:
            algo = dup[0]
            path = dup[1].split('/')[-5:]
            path = '/'.join(path)[:-3] # -3 removes .gz
            perc = dup[2]
            to_ret += "{}: {} [{}%]\n".format(path, algo, perc)
        self.p_duplicate = to_ret

        self.mispObject = AilleakObject(self.moduleName, self.p_source, self.p_date, self.p_content, self.p_duplicate, self.p_duplicate_number)

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

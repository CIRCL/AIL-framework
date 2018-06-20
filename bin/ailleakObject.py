#!/usr/bin/env python3
# -*-coding:UTF-8 -*

from pymisp.tools.abstractgenerator import AbstractMISPObjectGenerator
import configparser
from packages import Paste
import datetime
import json
from io import BytesIO

class AilLeakObject(AbstractMISPObjectGenerator):
    def __init__(self, uuid_ail, p_source, p_date, p_content, p_duplicate, p_duplicate_number):
        super(AbstractMISPObjectGenerator, self).__init__('ail-leak')
        self._uuid = uuid_ail
        self._p_source = p_source
        self._p_date = p_date
        self._p_content = p_content
        self._p_duplicate = p_duplicate
        self._p_duplicate_number = p_duplicate_number
        self.generate_attributes()

    def generate_attributes(self):
        self.add_attribute('origin', value=self._p_source, type='text')
        self.add_attribute('last-seen', value=self._p_date, type='datetime')
        if self._p_duplicate_number > 0:
            self.add_attribute('duplicate', value=self._p_duplicate, type='text')
            self.add_attribute('duplicate_number', value=self._p_duplicate_number, type='counter')
        self._pseudofile = BytesIO(self._p_content.encode())
        res = self.add_attribute('raw-data', value=self._p_source, data=self._pseudofile, type="attachment")# , ShadowAttribute=self.p_tag)
        #res.add_shadow_attributes(tag)
        self.add_attribute('sensor', value=self._uuid, type="text")

class ObjectWrapper:
    def __init__(self, pymisp):
        self.pymisp = pymisp
        self.currentID_date = None
        self.eventID_to_push = self.get_daily_event_id()
        cfg = configparser.ConfigParser()
        cfg.read('./packages/config.cfg')
        self.maxDuplicateToPushToMISP = cfg.getint("ailleakObject", "maxDuplicateToPushToMISP")
        self.attribute_to_tag = None

    def add_new_object(self, uuid_ail, path, p_source, tag):
        self.uuid_ail = uuid_ail
        self.path = path
        self.p_source = p_source
        self.paste = Paste.Paste(path)
        self.p_date = self.date_to_str(self.paste.p_date)
        self.p_content = self.paste.get_p_content()
        self.p_tag = tag

        temp = self.paste._get_p_duplicate()

        #beautifier
        if not temp:
            temp = ''

        p_duplicate_number = len(temp) if len(temp) >= 0 else 0

        to_ret = ""
        for dup in temp[:10]:
            dup = dup.replace('\'','\"').replace('(','[').replace(')',']')
            dup = json.loads(dup)
            algo = dup[0]
            path = dup[1].split('/')[-6:]
            path = '/'.join(path)[:-3] # -3 removes .gz
            if algo == 'tlsh':
                perc = 100 - int(dup[2])
            else:
                perc = dup[2]
            to_ret += "{}: {} [{}%]\n".format(path, algo, perc)
        p_duplicate = to_ret

        self.mispObject = AilLeakObject(self.uuid_ail, self.p_source, self.p_date, self.p_content, p_duplicate, p_duplicate_number)

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
        eventUuid = event['Event']['uuid']
        self.pymisp.tag(eventUuid, 'infoleak:output-format="ail-daily"')
        return event

    # Publish object to MISP
    def pushToMISP(self, uuid_ail, path, tag):
        self._p_source = path.split('/')[-5:]
        self._p_source = '/'.join(self._p_source)[:-3]

        if self.currentID_date != datetime.date.today(): #refresh id
            self.eventID_to_push = self.get_daily_event_id()

        mispTYPE = 'ail-leak'

        # paste object already exist
        if self.paste_object_exist(self.eventID_to_push, self._p_source):
            # add new tag
            self.tag(self.attribute_to_tag, tag)
            print(self._p_source + ' tagged: ' + tag)
        #create object
        else:
            self.add_new_object(uuid_ail, path, self._p_source, tag)


            try:
                templateID = [x['ObjectTemplate']['id'] for x in self.pymisp.get_object_templates_list() if x['ObjectTemplate']['name'] == mispTYPE][0]
            except IndexError:
                valid_types = ", ".join([x['ObjectTemplate']['name'] for x in self.pymisp.get_object_templates_list()])
                print ("Template for type %s not found! Valid types are: %s" % (mispTYPE, valid_types))
            r = self.pymisp.add_object(self.eventID_to_push, templateID, self.mispObject)
            if 'errors' in r:
                print(r)
            else:
                # tag new object
                self.set_attribute_to_tag_uuid(self.eventID_to_push, self._p_source)
                self.tag(self.attribute_to_tag, tag)
                print('Pushed:', tag, '->', self._p_source)

    def paste_object_exist(self, eventId, source):
        res = self.pymisp.search(controller='attributes', eventid=eventId, values=source)
        # object already exist
        if res['response']:
            self.attribute_to_tag = res['response']['Attribute'][0]['uuid']
            return True
        # new object
        else:
            return False

    def set_attribute_to_tag_uuid(self, eventId, source):
        res = self.pymisp.search(controller='attributes', eventid=eventId, values=source)
        self.attribute_to_tag = res['response']['Attribute'][0]['uuid']

    def tag(self, uuid, tag):
        self.pymisp.tag(uuid, tag)

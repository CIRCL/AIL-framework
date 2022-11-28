#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from pymisp import MISPEvent, MISPObject
from pymisp.tools.abstractgenerator import AbstractMISPObjectGenerator

import datetime

from lib.objects.Items import Item
from lib import ConfigLoader

class ObjectWrapper:
    def __init__(self, pymisp):
        self.pymisp = pymisp
        self.currentID_date = None
        self.eventID_to_push = self.get_daily_event_id()
        config_loader = ConfigLoader.ConfigLoader()
        self.maxDuplicateToPushToMISP = config_loader.get_config_int("ailleakObject", "maxDuplicateToPushToMISP")
        config_loader = None
        self.attribute_to_tag = None

    def add_new_object(self, uuid_ail, item_id):
        self.uuid_ail = uuid_ail

        item = Item(item_id)
        return item.get_misp_object()

    def date_to_str(self, date):
        return "{0}-{1}-{2}".format(date.year, date.month, date.day)

    def get_all_related_events(self, to_search):
        result = self.pymisp.search(controller='events', eventinfo=to_search, metadata=False)
        events = []
        if result:
            for e in result:
                events.append({'id': e['Event']['id'], 'org_id': e['Event']['org_id'], 'info': e['Event']['info']})
        return events

    def get_daily_event_id(self):
        to_match = "Daily AIL-leaks {}".format(datetime.date.today())
        events = self.get_all_related_events(to_match)
        for dic in events:
            info = dic['info']
            e_id = dic['id']
            if info == to_match:
                print('Found: ', info, '->', e_id)
                self.currentID_date = datetime.date.today()
                return e_id
        created_event = self.create_daily_event()
        new_id = created_event['Event']['id']
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

        event = MISPEvent()
        event.distribution = distribution
        event.info = info
        event.analysis = analysis
        event.threat = threat
        event.published = published

        event.add_tag('infoleak:output-format="ail-daily"')
        existing_event = self.pymisp.add_event(event)
        return existing_event

    # Publish object to MISP
    def pushToMISP(self, uuid_ail, item_id, tag):

        if self.currentID_date != datetime.date.today(): #refresh id
            self.eventID_to_push = self.get_daily_event_id()

        mispTYPE = 'ail-leak'

        # paste object already exist
        if self.paste_object_exist(self.eventID_to_push, item_id):
            # add new tag
            self.tag(self.attribute_to_tag, tag)
            print(item_id + ' tagged: ' + tag)
        # create object
        else:
            misp_obj = self.add_new_object(uuid_ail, item_id)

            # deprecated
            # try:
            #     templateID = [x['ObjectTemplate']['id'] for x in self.pymisp.get_object_templates_list() if x['ObjectTemplate']['name'] == mispTYPE][0]
            # except IndexError:
            #     valid_types = ", ".join([x['ObjectTemplate']['name'] for x in self.pymisp.get_object_templates_list()])
            #     print ("Template for type %s not found! Valid types are: %s" % (mispTYPE, valid_types))


            r = self.pymisp.add_object(self.eventID_to_push, misp_obj, pythonify=True)
            if 'errors' in r:
                print(r)
            else:
                print('Pushed:', tag, '->', item_id)

    def paste_object_exist(self, eventId, item_id):
        res = self.pymisp.search(controller='attributes', eventid=eventId, value=item_id)
        # object already exist
        if res.get('Attribute', []):
            self.attribute_to_tag = res['Attribute'][0]['uuid']
            return True
        # new object
        else:
            return False

    def tag(self, uuid, tag):
        self.pymisp.tag(uuid, tag)

#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import os
import datetime
import sys
import uuid

from abc import ABC

from pymisp import MISPEvent, PyMISP, PyMISPError
from urllib3 import disable_warnings as urllib3_disable_warnings

sys.path.append('../../configs/keys')
sys.path.append(os.environ['AIL_BIN'])
#################################
# Import Project packages
#################################
from exporter.abstract_exporter import AbstractExporter
from lib.exceptions import MISPConnectionError
from lib.ConfigLoader import ConfigLoader
from lib.Investigations import Investigation
from lib.objects.abstract_object import AbstractObject
from lib.objects import ail_objects

# from lib.Tracker import Tracker

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

#### FUNCTIONS ####

def get_user_misp_objects_to_export(user_id):
    objs = []
    objects = r_db.hgetall(f'user:obj:misp:export:{user_id}')
    for obj in objects:
        obj_type, obj_subtype, obj_id = obj.split(':', 2)
        lvl = objects[obj]
        try:
            lvl = int(lvl)
        except(TypeError, ValueError):
            lvl = 0
        objs.append({'type': obj_type, 'subtype': obj_subtype, 'id': obj_id, 'lvl': lvl})
    return objs

def add_user_misp_object_to_export(user_id, obj_type, obj_subtype, obj_id, lvl=0):
    if not obj_subtype:
        obj_subtype = ''
    r_db.hset(f'user:obj:misp:export:{user_id}', f'{obj_type}:{obj_subtype}:{obj_id}', lvl)

def delete_user_misp_object_to_export(user_id, obj_type, obj_subtype, obj_id):
    r_db.hdel(f'user:obj:misp:export:{user_id}', f'{obj_type}:{obj_subtype}:{obj_id}')

def delete_user_misp_objects_to_export(user_id):
    r_db.delete(f'user:obj:misp:export:{user_id}')

# --- FUNCTIONS --- #

# MISPExporter -> return correct exporter by type ????
class MISPExporter(AbstractExporter, ABC):
    """MISP Exporter

    :param url: URL of the MISP instance you want to connect to
    :param key: API key of the user you want to use
    :param ssl: can be True or False (to check or to not check the validity of the certificate.
    Or a CA_BUNDLE in case of self signed or other certificate (the concatenation of all the crt of the chain)
    """

    def __init__(self, url='', key='', ssl=False):
        super().__init__()

        if url and key:
            self.url = url
            self.key = key
            self.ssl = ssl
            if self.ssl is False:
                urllib3_disable_warnings()
        elif url or key:
            raise Exception('Error: missing url or api key')
        else:
            self.url = None
            self.key = None
            self.ssl = None
            # try:
            #     from mispKEYS import misp_url, misp_key, misp_verifycert
            #     self.url = misp_url
            #     self.key = misp_key
            #     self.ssl = misp_verifycert
            #     if self.ssl is False:
            #         urllib3_disable_warnings()
            #     if self.url.endswith('/'):
            #         self.url = self.url[:-1]
            # except Exception:  # ModuleNotFoundError
            #     self.url = None
            #     self.key = None
            #     self.ssl = None

    def get_misp(self):
        try:
            misp = PyMISP(self.url, self.key, self.ssl)
        except PyMISPError as e:
            raise MISPConnectionError(e.message)
        return misp

    # TODO catch exception
    def get_misp_uuid(self):
        misp = self.get_misp()
        misp_setting = misp.get_server_setting('MISP.uuid')
        return misp_setting.get('value')

    # TODO ADD TIMEOUT
    # TODO return error
    def ping_misp(self):
        try:
            self.get_misp()
            return True
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def sanitize_distribution(distribution):
        try:
            distribution = int(distribution)
            if 0 <= distribution <= 3:
                return distribution
            else:
                return 0
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def sanitize_threat_level(threat_level):
        try:
            threat_level = int(threat_level)
            if 1 <= threat_level <= 4:
                return threat_level
            else:
                return 4
        except (TypeError, ValueError):
            return 4

    @staticmethod
    def sanitize_analysis(analysis):
        try:
            analysis = int(analysis)
            if 0 <= analysis <= 2:
                return analysis
            else:
                return 0
        except (TypeError, ValueError):
            return 0

    def get_event_object_id(self, event_id, obj):
        misp = self.get_misp()
        resp = misp.search(controller='attributes', eventid=event_id, value=obj.get_id())
        attribute = resp.get('Attribute', [])
        if attribute:
            return attribute[0]['object_id']

    def add_event_object_tag(self, obj_id, tag):
        misp = self.get_misp()
        misp_obj = misp.get_object(obj_id, pythonify=True)
        for attribute in misp_obj.attributes:
            attribute.add_tag(tag)
            misp.update_attribute(attribute)

    def add_event_object(self, event_id, obj):
        misp_object = obj.get_misp_object()
        misp = self.get_misp()
        misp.add_object(event_id, misp_object)

    def get_daily_event_id(self):
        misp = self.get_misp()
        event_info = f'Daily AIL-leaks {datetime.date.today()}'
        resp = misp.search(controller='events', eventinfo=event_info, metadata=True)
        if resp:
            return resp[0]['Event']['id']
        else:
            misp_event = self.create_event([], info=event_info, threat_level=3, export=True)
            return misp_event['Event']['id']

    # TODO EVENT REPORT ???????
    def create_event(self, objs, export=False, event_uuid=None, date=None, publish=False, info=None, tags=None,
                     analysis=0, distribution=0, threat_level=4):
        if tags is None:
            tags = []
        event = MISPEvent()
        if not event_uuid:
            event_uuid = str(uuid.uuid4())
        event.uuid = event_uuid
        if date:
            event.date = date
        if not info:
            info = 'AIL framework export'
        event.info = info
        if publish:
            event.publish()
        for tag in tags:
            event.add_tag(tag)
        event.distribution = self.sanitize_distribution(distribution)
        event.threat_level_id = self.sanitize_threat_level(threat_level)
        event.analysis = self.sanitize_analysis(analysis)

        misp_objects = ail_objects.get_misp_objects(objs)
        for obj in misp_objects:
            if obj:
                event.add_object(obj)
        # print(event.to_json())

        if export and self.url:
            misp = self.get_misp()
            misp_event = misp.add_event(event)
            # TODO: handle error

            misp_event['url'] = f'{self.url}/events/view/{misp_event["Event"]["uuid"]}'
            return misp_event
        else:
            return event.to_json()
            # return {'uuid': event['uuid'], 'event': event.to_json()}

        # EXPORTER CHAIN
        # if self.chainable
        # if self.next_exporter:
        #     next_exporter.export({'type': 'misp_event', 'data': {'event': misp_event}})

    def __repr__(self):
        return f'<{self.__class__.__name__}(url={self.url})'

class MISPExporterAILObjects(MISPExporter):
    """MISPExporter AILObjects

    :param url: URL of the MISP instance you want to connect to :param key: API key of the user you want to use
    :param ssl: can be True or False (to check or to not check the validity of the certificate. Or a CA_BUNDLE in
    case of self signed or other certificate (the concatenation of all the crt of the chain)
    """

    def __init__(self, url='', key='', ssl=False):
        super().__init__(url=url, key=key, ssl=ssl)

    def export(self, objects, export=False, event_uuid=None, date=None, publish=False, info=None, tags=[],
               analysis=0, distribution=0, threat_level=4):
        """Export a list of AILObjects as a MISP event

        :param objects: Investigation object or investigation uuid string
        :type objects: list[AbstractObject]
        """
        # objects ????
        # TODO convert string tuple to object

        return self.create_event(objects, event_uuid=event_uuid, date=date, publish=publish,
                                 analysis=analysis, distribution=distribution, threat_level=threat_level,
                                 info=info, tags=tags, export=export)

class MISPExporterInvestigation(MISPExporter):
    """MISPExporter Investigation

    :param url: URL of the MISP instance you want to connect to :param key: API key of the user you want to use
    :param ssl: can be True or False (to check or to not check the validity of the certificate. Or a CA_BUNDLE in
    case of self signed or other certificate (the concatenation of all the crt of the chain)
    """

    def __init__(self, url='', key='', ssl=False):
        super().__init__(url=url, key=key, ssl=ssl)

    def export(self, investigation):
        """Export an Investigation as a MISP event

        :param investigation: Investigation object or investigation uuid string
        :type investigation: Investigation | str
        """
        if not isinstance(investigation, Investigation):
            investigation = Investigation(investigation)
        objs = ail_objects.get_objects(investigation.get_objects())
        event = self.create_event(objs,
                                  date=investigation.get_date(),
                                  distribution=0,
                                  threat_level=investigation.get_threat_level(),
                                  analysis=investigation.get_analysis(),
                                  info=investigation.get_info(),
                                  tags=investigation.get_tags(),
                                  export=True)
        return event


class MISPExporterTrackerMatch(MISPExporter):
    """MISPExporter Tracker match

    :param url: URL of the MISP instance you want to connect to
    :param key: API key of the user you want to use
    :param ssl: can be True or False (to check or to not check the validity of the certificate. Or a CA_BUNDLE in case of self signed or other certificate (the concatenation of all the crt of the chain)
    """

    def __init__(self, url='', key='', ssl=False):
        super().__init__(url=url, key=key, ssl=ssl)

    # TODO
    def export(self, tracker, item):
        pass


class MISPExporterAutoDaily(MISPExporter):
    """MISPExporter AILObjects

    :param url: URL of the MISP instance you want to connect to :param key: API key of the user you want to use
    :param ssl: can be True or False (to check or to not check the validity of the certificate. Or a CA_BUNDLE in
    case of self signed or other certificate (the concatenation of all the crt of the chain)
    """

    def __init__(self, url='', key='', ssl=False):
        super().__init__(url=url, key=key, ssl=ssl)

        self.event_id = - 1
        self.date = datetime.date.today()

    def export(self, obj, tag):
        """Export a list of AILObjects as a MISP event

        :param obj: AIL Object to export
        :type obj: AbstractObject
        """
        try:
            if self.date != datetime.date.today() or int(self.event_id) < 0:
                self.date = datetime.date.today()
                self.event_id = self.get_daily_event_id()

            obj_id = self.get_event_object_id(self.event_id, obj)
            # Object already in event
            if obj_id:
                self.add_event_object_tag(obj_id, tag)
            else:
                self.add_event_object(self.event_id, obj)

        except MISPConnectionError:
            self.event_id = - 1
            return -1


if __name__ == '__main__':
    # exporter = MISPExporterAILObjects()
    # from lib.objects.Cves import Cve
    from lib.objects.Items import Item
    # objs_t = [Item('crawled/2020/09/14/circl.lu0f4976a4-dda4-4189-ba11-6618c4a8c951'),
    #           Cve('CVE-2020-16856'), Cve('CVE-2014-6585'), Cve('CVE-2015-0383'),
    #           Cve('CVE-2015-0410')]
    # r = exporter.export(objs_t, export=False)
    # print(r)

    # r = exporter.get_misp_uuid()
    # r = misp.server_settings()
    # for item in r['finalSettings']:
    #     print()
    #     print(item)
    #     # print(r['finalSettings'][item])
    #     # print()
    #     print()

    obj = Item('submitted/2023/05/15/submitted_aed90c6f-c620-4437-93d7-5ff17d1a8eef.gz')
    obj = Item('submitted/2023/05/15/submitted_8a6136c2-c7f2-4c9e-8f29-e1a62315b482.gz')
    tag = 'infoleak:automatic-detection="credit-card"'
    exporter = MISPExporterAutoDaily()
    exporter.export(obj, tag)

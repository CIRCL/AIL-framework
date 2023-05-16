#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import os
import sys
import uuid

from abc import ABC

from thehive4py.api import TheHiveApi
from thehive4py.models import Alert, AlertArtifact, Case, CaseObservable
import thehive4py.exceptions
from urllib3 import disable_warnings as urllib3_disable_warnings

sys.path.append('../../configs/keys')
sys.path.append(os.environ['AIL_BIN'])
#################################
# Import Project packages
#################################
from exporter.abstract_exporter import AbstractExporter
from lib.ConfigLoader import ConfigLoader
from lib.ail_core import get_ail_uuid
from lib.objects.Items import Item
# from lib.objects.abstract_object import AbstractObject

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
config_loader = None

#### FUNCTIONS ####

# --- FUNCTIONS --- #

# MISPExporter -> return correct exporter by type ????
class TheHiveExporter(AbstractExporter, ABC):
    """TheHive Exporter

    :param url: URL of the Hive instance you want to connect to
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
            try:
                from theHiveKEYS import the_hive_url, the_hive_key, the_hive_verifycert
                self.url = the_hive_url
                self.key = the_hive_key
                self.ssl = the_hive_verifycert
                if self.ssl is False:
                    urllib3_disable_warnings()
                if self.url.endswith('/'):
                    self.url = self.url[:-1]
            except ModuleNotFoundError:
                self.url = None
                self.key = None
                self.ssl = None

    def get_hive(self):
        return TheHiveApi(self.url, self.key, cert=self.ssl)

    # TODO ADD TIMEOUT
    # TODO return error
    def ping(self):
        try:
            self.get_hive().get_alert('0')
            return True
        except thehive4py.exceptions.AlertException:
            return False

    @staticmethod
    def sanitize_threat_level(threat_level):
        try:
            int(threat_level)
            if 1 <= threat_level <= 3:
                return threat_level
            else:
                return 2
        except (TypeError, ValueError):
            return 2

    @staticmethod
    def sanitize_tlp(tlp):
        try:
            int(tlp)
            if 0 <= tlp <= 3:
                return tlp
            else:
                return 2
        except (TypeError, ValueError):
            return 2

    @staticmethod
    def sanitize_analysis(analysis):
        try:
            int(analysis)
            if 0 <= analysis <= 2:
                return analysis
            else:
                return 0
        except (TypeError, ValueError):
            return 0

    def get_case_url(self, case_id):
        return f'{self.url}/cases/{case_id}/details'

    def create_alert(self, artifacts, source, description='AIL', source_ref=None, tags=None, tlp=3, type='ail'):
        if not source_ref:
            source_ref = str(uuid.uuid4())[0:6]
        if tags is None:
            tags = []

        alert = Alert(title='AIL Leak',
                      tlp=self.sanitize_tlp(tlp),
                      tags=tags,
                      description=description,
                      type=type,
                      source=source,
                      sourceRef=source_ref,
                      artifacts=artifacts)

        # Create the Alert
        alert_id = 0
        try:
            req = self.get_hive().create_alert(alert)
            if req.status_code == 201:
                # print(json.dumps(req.json(), indent=4, sort_keys=True))
                print('Alert Created')
                # print(req.json())
                alert_id = req.json()['id']
            else:
                # TODO LOGS
                print(f'ko: {req.status_code}/{req.text}')
                return -2
        except Exception as e:
            print(e)
            print('hive connection error')
            return -1
        return alert_id

    def create_case(self, observables, description=None, tags=None, title=None, threat_level=2, tlp=2):
        if tags is None:
            tags = []

        case = Case(title=title,
                    tlp=self.sanitize_tlp(tlp),
                    severity=self.sanitize_threat_level(threat_level),
                    flag=False,
                    tags=tags,
                    description=description)

        # Create Case
        thehive = self.get_hive()
        resp = thehive.create_case(case)
        if resp.status_code == 201:
            case_id = resp.json()['id']

            for observable in observables:
                resp_o = thehive.create_case_observable(case_id, observable)
                if resp_o.status_code != 201:
                    # TODO LOGS
                    print(f'error observable creation: {resp_o.status_code}/{resp_o.text}')
            # print(case_id)
            # return HIVE_URL /thehive/cases/~37040/details
            return case_id
        else:
            # TODO LOGS
            print(f'ko: {resp.status_code}/{resp.text}')
            return None

    def __repr__(self):
        return f'<{self.__class__.__name__}(url={self.url})'


class TheHiveExporterAlertTag(TheHiveExporter):
    """TheHiveExporterAlertTag TagTrigger

    :param url: URL of the Hive instance you want to connect to
    :param key: API key of the user you want to use
    :param ssl: can be True or False (to check or to not check the validity of the certificate. Or a CA_BUNDLE in case of self signed or other certificate (the concatenation of all the crt of the chain)
    """

    def __init__(self, url='', key='', ssl=False):
        super().__init__(url=url, key=key, ssl=ssl)

    def export(self, item, tag):
        item_id = item.get_id()
        tags = list(item.get_tags())

        # remove .gz from submitted path to TheHive because content is decompressed
        if item_id.endswith(".gz"):
            item_id = item_id[:-3]
        # add .txt to make it easier to open when downloaded from TheHive
        item_id = f'{item_id}.txt'

        description = f'AIL Leak, triggered by {tag}'

        artifacts = [
            AlertArtifact(dataType='other', message='uuid-ail', data=(get_ail_uuid())),
            AlertArtifact(dataType='file', data=(item.get_raw_content(decompress=True), item_id), tags=tags)
        ]

        return self.create_alert(artifacts, description=description, source=item.get_source(), tags=tags)


class TheHiveExporterItem(TheHiveExporter):
    """TheHiveExporter Item case

    :param url: URL of the Hive instance you want to connect to
    :param key: API key of the user you want to use
    :param ssl: can be True or False (to check or to not check the validity of the certificate. Or a CA_BUNDLE in case of self signed or other certificate (the concatenation of all the crt of the chain)
    """

    def __init__(self, url='', key='', ssl=False):
        super().__init__(url=url, key=key, ssl=ssl)

    def export(self, item_id, description=None, title=None, threat_level=None, tlp=None):
        item = Item(item_id)
        date = item.get_date()
        date = f'{date[0:4]}-{date[4:6]}-{date[6:8]}'
        tags = item.get_tags()
        ail_uuid = get_ail_uuid()

        if not title:
            title = f'AIL Case {item.id}'
        if not description:
            description = f'AIL {ail_uuid} Case'

        observables = [
            CaseObservable(dataType="other", data=[ail_uuid], message="uuid-ail"),
            CaseObservable(dataType="file", data=item.get_filename(), tags=tags),
            CaseObservable(dataType="other", data=[item.get_source()], message="source"),
            CaseObservable(dataType="other", data=[date], message="last-seen")
        ]

        case_id = self.create_case(observables, tags=tags, description=description, title=title,
                                   threat_level=threat_level, tlp=tlp)

        # SAVE CASE URL/ID ????

        return case_id


# if __name__ == '__main__':

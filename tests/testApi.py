#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import unittest

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'bin'))
sys.path.append(os.environ['AIL_FLASK'])
sys.path.append(os.path.join(os.environ['AIL_FLASK'], 'modules'))

import Import_helper
import Tag

from Flask_server import app

def parse_response(obj, ail_response):
    res_json = ail_response.get_json()
    if 'status' in res_json:
        if res_json['status'] == 'error':
            return obj.fail('{}: {}: {}'.format(ail_response.status_code, res_json['status'], res_json['reason']))
    return res_json

def get_api_key():
    api_file = os.path.join(os.environ['AIL_HOME'], 'DEFAULT_PASSWORD')
    if os.path.isfile(api_file):
        with open(os.path.join(os.environ['AIL_HOME'], 'DEFAULT_PASSWORD'), 'r') as f:
            content = f.read()
            content = content.splitlines()
            apikey = content[-1]
            apikey = apikey.replace('API_Key=', '', 1)
    # manual tests
    else:
        apikey = sys.argv[1]
    return apikey

APIKEY = get_api_key()

class TestApiV1(unittest.TestCase):
    import_uuid = None
    item_id = None


    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.apikey = APIKEY
        self.item_content = "text to import"
        self.item_tags = ["infoleak:analyst-detection=\"private-key\""]
        self.expected_tags = ["infoleak:analyst-detection=\"private-key\"", 'infoleak:submission="manual"']

    # POST /api/v1/import/item
    def test_0001_api_import_item(self):
        input_json = {"type": "text","tags": self.item_tags,"text": self.item_content}
        req = self.client.post('/api/v1/import/item', json=input_json ,headers={ 'Authorization': self.apikey })
        req_json = parse_response(self, req)
        import_uuid = req_json['uuid']
        self.__class__.import_uuid = import_uuid
        self.assertTrue(Import_helper.is_valid_uuid_v4(import_uuid))

    # POST /api/v1/get/import/item
    def test_0002_api_get_import_item(self):
        input_json = {"uuid": self.__class__.import_uuid}
        item_not_imported = True
        import_timout = 30
        start = time.time()

        while item_not_imported:
            req = self.client.post('/api/v1/get/import/item', json=input_json ,headers={ 'Authorization': self.apikey })
            req_json = parse_response(self, req)
            if req_json['status'] == 'imported':
                try:
                    item_id = req_json['items'][0]
                    item_not_imported = False
                except Exception as e:
                    if time.time() - start > import_timout:
                        item_not_imported = False
                        self.fail("Import error: {}".format(req_json))
            else:
                if time.time() - start > import_timout:
                    item_not_imported = False
                    self.fail("Import Timeout, import status: {}".format(req_json['status']))
        self.__class__.item_id = item_id

        # Process item
        time.sleep(5)

    # POST /api/v1/get/item/content
    def test_0003_api_get_item_content(self):
        input_json = {"id": self.__class__.item_id}
        req = self.client.post('/api/v1/get/item/content', json=input_json ,headers={ 'Authorization': self.apikey })
        req_json = parse_response(self, req)
        item_content = req_json['content']
        self.assertEqual(item_content, self.item_content)

    # POST /api/v1/get/item/tag
    def test_0004_api_get_item_tag(self):
        input_json = {"id": self.__class__.item_id}
        req = self.client.post('/api/v1/get/item/tag', json=input_json ,headers={ 'Authorization': self.apikey })
        req_json = parse_response(self, req)
        item_tags = req_json['tags']
        self.assertCountEqual(item_tags, self.expected_tags)

    # POST /api/v1/get/item/tag
    def test_0005_api_get_item_default(self):
        input_json = {"id": self.__class__.item_id}
        req = self.client.post('/api/v1/get/item/default', json=input_json ,headers={ 'Authorization': self.apikey })
        req_json = parse_response(self, req)
        item_tags = req_json['tags']
        self.assertCountEqual(item_tags, self.expected_tags)
        item_content = req_json['content']
        self.assertEqual(item_content, self.item_content)

    # POST /api/v1/get/item/tag
    # # TODO: add more test
    def test_0006_api_get_item(self):
        input_json = {"id": self.__class__.item_id, "content": True}
        req = self.client.post('/api/v1/get/item', json=input_json ,headers={ 'Authorization': self.apikey })
        req_json = parse_response(self, req)
        item_tags = req_json['tags']
        self.assertCountEqual(item_tags, self.expected_tags)
        item_content = req_json['content']
        self.assertEqual(item_content, self.item_content)

    # POST api/v1/add/item/tag
    def test_0007_api_add_item_tag(self):
        tags_to_add = ["infoleak:analyst-detection=\"api-key\""]
        current_item_tag = Tag.get_item_tags(self.__class__.item_id)
        current_item_tag.append(tags_to_add[0])

        #galaxy_to_add = ["misp-galaxy:stealer=\"Vidar\""]
        input_json = {"id": self.__class__.item_id, "tags": tags_to_add}
        req = self.client.post('/api/v1/add/item/tag', json=input_json ,headers={ 'Authorization': self.apikey })
        req_json = parse_response(self, req)
        item_tags = req_json['tags']
        self.assertEqual(item_tags, tags_to_add)

        new_item_tag = Tag.get_item_tags(self.__class__.item_id)
        self.assertCountEqual(new_item_tag, current_item_tag)

    # DELETE api/v1/delete/item/tag
    def test_0008_api_add_item_tag(self):
        tags_to_delete = ["infoleak:analyst-detection=\"api-key\""]
        input_json = {"id": self.__class__.item_id, "tags": tags_to_delete}
        req = self.client.delete('/api/v1/delete/item/tag', json=input_json ,headers={ 'Authorization': self.apikey })
        req_json = parse_response(self, req)
        item_tags = req_json['tags']
        self.assertCountEqual(item_tags, tags_to_delete)
        current_item_tag = Tag.get_item_tags(self.__class__.item_id)
        if tags_to_delete[0] in current_item_tag:
            self.fail('Tag no deleted')

    # POST api/v1/get/tag/metadata
    def test_0009_api_add_item_tag(self):
        input_json = {"tag": self.item_tags[0]}
        req = self.client.post('/api/v1/get/tag/metadata', json=input_json ,headers={ 'Authorization': self.apikey })
        req_json = parse_response(self, req)
        self.assertEqual(req_json['tag'], self.item_tags[0])

    # GET api/v1/get/tag/all
    def test_0010_api_add_item_tag(self):
        input_json = {"tag": self.item_tags[0]}
        req = self.client.get('/api/v1/get/tag/all', json=input_json ,headers={ 'Authorization': self.apikey })
        req_json = parse_response(self, req)
        self.assertTrue(req_json['tags'])

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

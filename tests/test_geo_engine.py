#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('AIL_BIN', os.path.join(os.getcwd(), 'bin'))
os.environ.setdefault('AIL_HOME', os.getcwd())

sys.path.append(os.environ['AIL_BIN'])

from lib import geo_engine
from lib.objects.abstract_object import AbstractObject


class FakeGeoRedis:

    def __init__(self):
        self.hashes = {}
        self.geo_zsets = {}

    def hset(self, key, field, value):
        if key not in self.hashes:
            self.hashes[key] = {}
        is_new = field not in self.hashes[key]
        self.hashes[key][field] = str(value)
        return 1 if is_new else 0

    def hget(self, key, field):
        return self.hashes.get(key, {}).get(field)

    def zcard(self, key):
        return len(self.geo_zsets.get(key, {}))

    def zrange(self, key, start, end):
        members = list(self.geo_zsets.get(key, {}).keys())
        if end == -1:
            return members[start:]
        return members[start:end + 1]

    def zrem(self, key, *members):
        if key not in self.geo_zsets:
            return 0
        removed = 0
        for member in members:
            if member in self.geo_zsets[key]:
                del self.geo_zsets[key][member]
                removed += 1
        return removed

    def delete(self, *keys):
        removed = 0
        for key in keys:
            if key in self.hashes:
                del self.hashes[key]
                removed += 1
            if key in self.geo_zsets:
                del self.geo_zsets[key]
                removed += 1
        return removed

    def geoadd(self, key, values):
        lon, lat, member = values
        if key not in self.geo_zsets:
            self.geo_zsets[key] = {}
        self.geo_zsets[key][member] = (str(lon), str(lat))
        return 1

    def geopos(self, key, *members):
        res = []
        for member in members:
            res.append(self.geo_zsets.get(key, {}).get(member))
        return res


class DummyObject(AbstractObject):
    def get_content(self):
        return None


class TestGeoEngine(unittest.TestCase):

    def setUp(self):
        self.fake_geo = FakeGeoRedis()
        geo_engine.r_geo = self.fake_geo

    def test_add_one_geo(self):
        with patch('lib.geo_engine.ail_core.generate_uuid', return_value='11111111-1111-4111-8111-111111111111'):
            geo_id = geo_engine.add_geo_to_object('item::id-1', 'item', 1.0, 2.0, probability=0.8)

        self.assertEqual(geo_id, '11111111111141118111111111111111')
        self.assertEqual(self.fake_geo.hget(f'g:{geo_id}', 'o'), 'item::id-1')
        self.assertEqual(self.fake_geo.hget(f'g:{geo_id}', 'p'), '0.8')
        self.assertEqual(self.fake_geo.zcard('o:item::id-1'), 1)
        self.assertEqual(self.fake_geo.zcard('objs:item'), 1)

    def test_add_two_geos_same_object(self):
        geo_engine.add_geo_to_object('item::id-2', 'item', 3.0, 4.0, geo_id='geo-A')
        geo_engine.add_geo_to_object('item::id-2', 'item', 5.0, 6.0, geo_id='geo-B')

        self.assertTrue(geo_engine.object_has_geo('item::id-2'))
        self.assertEqual(self.fake_geo.zcard('o:item::id-2'), 2)
        self.assertEqual(geo_engine.get_geo_position('item::id-2', 'geo-A'), [('3.0', '4.0')])

    def test_same_coordinates_different_objects(self):
        geo_engine.add_geo_to_object('item::id-3', 'item', 7.0, 8.0, geo_id='geo-C')
        geo_engine.add_geo_to_object('domain::id-4', 'domain', 7.0, 8.0, geo_id='geo-D')

        self.assertEqual(self.fake_geo.zcard('o:item::id-3'), 1)
        self.assertEqual(self.fake_geo.zcard('o:domain::id-4'), 1)
        self.assertNotEqual(geo_engine.get_geo_object_gid('geo-C'), geo_engine.get_geo_object_gid('geo-D'))

    def test_remove_one_geo(self):
        geo_engine.add_geo_to_object('item::id-5', 'item', 1.2, 3.4, geo_id='geo-E')
        removed = geo_engine.remove_geo_from_object('item::id-5', 'item', 'geo-E')

        self.assertTrue(removed)
        self.assertFalse(geo_engine.object_has_geo('item::id-5'))
        self.assertIsNone(geo_engine.get_geo_object_gid('geo-E'))

    def test_object_with_no_geo(self):
        self.assertFalse(geo_engine.object_has_geo('item::missing'))
        self.assertEqual(geo_engine.delete_all_geo_from_object('item::missing', 'item'), 0)

    def test_delete_all_geos(self):
        geo_engine.add_geo_to_object('item::id-6', 'item', 9.0, 10.0, geo_id='geo-F')
        geo_engine.add_geo_to_object('item::id-6', 'item', 11.0, 12.0, geo_id='geo-G')

        removed = geo_engine.delete_all_geo_from_object('item::id-6', 'item')
        self.assertEqual(removed, 2)
        self.assertFalse(geo_engine.object_has_geo('item::id-6'))
        self.assertIsNone(geo_engine.get_geo_object_gid('geo-F'))
        self.assertIsNone(geo_engine.get_geo_object_gid('geo-G'))

    def test_get_all_geo_positions(self):
        geo_engine.add_geo_to_object('item::id-7', 'item', 2.1, 3.2, geo_id='geo-I')
        geo_engine.add_geo_to_object('item::id-7', 'item', 4.3, 5.4, geo_id='geo-J')

        geos = geo_engine.get_all_geo_positions('item::id-7')
        self.assertEqual(len(geos), 2)
        self.assertEqual(geos[0]['geo_id'], 'geo-I')
        self.assertEqual(geos[0]['position'], ('2.1', '3.2'))

    def test_get_object_nb_geos(self):
        geo_engine.add_geo_to_object('item::id-8', 'item', 1.0, 1.0, geo_id='geo-K')
        geo_engine.add_geo_to_object('item::id-8', 'item', 2.0, 2.0, geo_id='geo-L')

        self.assertEqual(geo_engine.get_object_nb_geos('item::id-8'), 2)

    def test_yield_objects_type_geos(self):
        geo_engine.add_geo_to_object('item::id-9', 'item', 9.1, 9.2, probability=0.7, geo_id='geo-M')
        geo_engine.add_geo_to_object('item::id-10', 'item', 10.1, 10.2, geo_id='geo-N')

        geos = list(geo_engine.yield_objects_type_geos('item'))
        geo_ids = {geo['geo_id'] for geo in geos}
        self.assertIn('geo-M', geo_ids)
        self.assertIn('geo-N', geo_ids)
        first = [geo for geo in geos if geo['geo_id'] == 'geo-M'][0]
        self.assertEqual(first['obj_gid'], 'item::id-9')
        self.assertEqual(first['position'], ('9.1', '9.2'))
        self.assertEqual(first['probability'], '0.7')

    def test_abstract_object_geo_methods(self):
        obj = DummyObject('item', 'obj-1')
        with patch('lib.objects.abstract_object.geo_engine.add_geo_to_object', return_value='geo-H') as m_add, \
             patch('lib.objects.abstract_object.geo_engine.remove_geo_from_object', return_value=True) as m_remove, \
             patch('lib.objects.abstract_object.geo_engine.object_has_geo', return_value=True) as m_has, \
             patch('lib.objects.abstract_object.geo_engine.delete_all_geo_from_object', return_value=1) as m_delete:

            self.assertEqual(obj.add_geo(1.0, 2.0, probability=0.5), 'geo-H')
            self.assertTrue(obj.remove_geo('geo-H'))
            self.assertTrue(obj.is_geo())
            self.assertEqual(obj.delete_geos(), 1)

            m_add.assert_called_once_with('item::obj-1', 'item', 1.0, 2.0, probability=0.5, geo_id=None)
            m_remove.assert_called_once_with('item::obj-1', 'item', 'geo-H')
            m_has.assert_called_once_with('item::obj-1')
            m_delete.assert_called_once_with('item::obj-1', 'item')


if __name__ == '__main__':
    unittest.main()

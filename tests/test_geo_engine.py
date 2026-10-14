#!/usr/bin/env python3
"""GEO validation and transactions, tested against an isolated Kvrocks instance."""

import ast
import configparser
import logging
from pathlib import Path
import sys
import unittest
import uuid
from abc import ABC, abstractmethod
from types import MethodType, ModuleType, SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from redis.exceptions import RedisError, WatchError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bin'))

from lib import geo_engine
from geo_test_helpers import IsolatedKvrocksTestCase


def load_object_class():
    tree = ast.parse((ROOT / 'bin/lib/objects/abstract_object.py').read_text())
    definition = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'AbstractObject')
    namespace = {'ABC': ABC, 'abstractmethod': abstractmethod, 'logging': logging, 'geo_engine': geo_engine, 'uuid': uuid,
                 'Tag': Mock(), 'delete_obj_correlations': Mock(), 'r_object': Mock()}
    exec(compile(ast.Module(body=[definition], type_ignores=[]), 'abstract_object.py', 'exec'), namespace)
    base = namespace['AbstractObject']
    methods = {name: lambda self, *args, **kwargs: None for name in base.__abstractmethods__}
    methods['exists'] = lambda self: self.present
    return type('TestObject', (base,), methods)


def load_object_method(path, class_name, method_name, namespace):
    tree = ast.parse((ROOT / path).read_text())
    definition = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    method = next(node for node in definition.body if isinstance(node, ast.FunctionDef) and node.name == method_name)
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[method_name]


def registered_object_methods(method_name):
    tree = ast.parse((ROOT / 'bin/lib/objects/ail_objects.py').read_text())
    imports = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'lib.objects':
            for alias in node.names:
                imports[alias.asname or alias.name] = (alias.name, None)
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('lib.objects.'):
            for alias in node.names:
                imports[alias.asname or alias.name] = (node.module.rsplit('.', 1)[1], alias.name)
    registry = next(node.value for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'OBJECTS_CLASS' for target in node.targets))
    for obj_type, classes in zip(registry.keys, registry.values):
        object_class = next(value for key, value in zip(classes.keys, classes.values) if key.value == 'obj')
        if isinstance(object_class, ast.Attribute):
            module = imports[object_class.value.id][0]
            class_name = object_class.attr
        else:
            module, class_name = imports[object_class.id]
        path = f'bin/lib/objects/{module}.py'
        object_tree = ast.parse((ROOT / path).read_text())
        definition = next(node for node in object_tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
        method = next(node for node in definition.body if isinstance(node, ast.FunctionDef) and node.name == method_name)
        yield obj_type.value, path, class_name, method


def stub_object_cleanup(obj):
    for name in ('delete_trackers', 'delete_retro_hunts', 'delete_investigations', 'delete_custom_meta', 'delete_translations', 'delete_languages', '_delete_metas', 'delete_dates', '_delete_daterange'):
        setattr(obj, name, Mock())


class GeoValidationTests(unittest.TestCase):
    def setUp(self):
        self.database = Mock()
        self.database_patch = patch.object(geo_engine, 'r_geo', self.database)
        self.database_patch.start()
        self.addCleanup(self.database_patch.stop)

    def test_valid_latitudes_are_clamped_only_at_index_boundary(self):
        for value, expected in ((0, 0), (49.6, 49.6), (90, geo_engine.GEO_MAX_LATITUDE), (-90, -geo_engine.GEO_MAX_LATITUDE)):
            with self.subTest(value=value):
                self.assertEqual(geo_engine.get_indexed_latitude(value), expected)
        self.database.pipeline.assert_not_called()

    def test_invalid_coordinates_do_not_access_database(self):
        for lon, lat in ((181, 0), (-181, 0), (0, 91), (0, -91), (float('nan'), 0), (0, float('inf')), (True, 0), (0, False), (None, 0), (0, 'invalid')):
            with self.subTest(longitude=lon, latitude=lat):
                with self.assertRaises(ValueError):
                    geo_engine.add_geo_to_object('item::test', 'item', lon, lat)
        self.database.pipeline.assert_not_called()

    def test_invalid_owners_and_type_mismatches_do_not_access_database(self):
        for gid, obj_type in ((None, 'item'), ('item:test', 'item'), ('item::', 'item'), ('Item::test', 'Item'), ('item::test\n', 'item'), ('item::test', 'message')):
            with self.subTest(gid=gid):
                with self.assertRaises(ValueError):
                    geo_engine.add_geo_to_object(gid, obj_type, 0, 0)
        self.database.pipeline.assert_not_called()

    def test_invalid_ids_and_pagination_do_not_access_database(self):
        for geo_id in (None, 'invalid', '0' * 32, 1):
            with self.subTest(geo_id=geo_id):
                with self.assertRaises(ValueError):
                    geo_engine.get_geo_from_object('item::test', geo_id)
        for offset, limit in ((-1, 100), (True, 100), (0, 0), (0, 1001), (0, True), (0, '100')):
            with self.subTest(offset=offset, limit=limit):
                with self.assertRaises(ValueError):
                    geo_engine.get_object_geos('item::test', offset=offset, limit=limit)
        self.database.assert_not_called()
        self.assertEqual(self.database.mock_calls, [])

    def test_connection_is_lazy_and_uses_dedicated_geo_configuration(self):
        config_module = ModuleType('lib.ConfigLoader')
        config_module.ConfigLoader = Mock()
        expected = config_module.ConfigLoader.return_value.get_db_conn.return_value
        with patch.dict(sys.modules, {'lib.ConfigLoader': config_module}), patch.object(geo_engine, 'r_geo', None):
            self.assertIs(geo_engine._get_geo_db(), expected)
            self.assertIs(geo_engine._get_geo_db(), expected)
        config_module.ConfigLoader.assert_called_once_with()
        config_module.ConfigLoader.return_value.get_db_conn.assert_called_once_with('Kvrocks_GEO')

    def test_invalid_connection_configuration_has_a_clear_error_and_can_be_retried(self):
        for error in (configparser.NoSectionError('Kvrocks_GEO'), configparser.NoOptionError('password', 'Kvrocks_GEO'), ValueError('invalid port')):
            with self.subTest(error=type(error).__name__):
                config_module = ModuleType('lib.ConfigLoader')
                config_module.ConfigLoader = Mock()
                connection = config_module.ConfigLoader.return_value.get_db_conn
                expected = Mock()
                connection.side_effect = [error, expected]
                with patch.dict(sys.modules, {'lib.ConfigLoader': config_module}), patch.object(geo_engine, 'r_geo', None):
                    with self.assertRaisesRegex(geo_engine.GeoConfigurationError, 'Update-conf.py'):
                        geo_engine._get_geo_db()
                    self.assertIsNone(geo_engine.r_geo)
                    self.assertIs(geo_engine._get_geo_db(), expected)

    def test_transactions_stop_after_bounded_conflict_retries(self):
        self.database.pipeline.return_value = MagicMock()
        self.database.pipeline.return_value.__enter__.return_value.watch.side_effect = WatchError
        with self.assertRaises(geo_engine.GeoConflictError):
            geo_engine.add_geo_to_object('item::test', 'item', 0, 0)
        self.assertEqual(self.database.pipeline.call_count, geo_engine.TRANSACTION_RETRIES)

    def test_sample_connection_matches_shipped_namespace(self):
        import configparser
        config = configparser.ConfigParser()
        config.read(ROOT / 'configs/core.cfg.sample')
        self.assertEqual(config.getint('Kvrocks_GEO', 'port'), 6383)
        self.assertIn(f"namespace.geo {config.get('Kvrocks_GEO', 'password')}", (ROOT / 'configs/6383.conf').read_text())


class ObjectGeoMethodsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load the actual base class without importing unrelated runtime databases/modules.
        cls.Object = load_object_class()

    def setUp(self):
        self.obj = self.Object('item', 'test')
        self.obj.present = True

    def test_geo_wrappers_pass_owner_and_coordinates(self):
        with patch.object(geo_engine, 'add_geo_to_object', return_value='geo') as add:
            self.assertEqual(self.obj.add_geo(6.1, 49.6), 'geo')
            add.assert_called_once_with('item::test', 'item', 6.1, 49.6, geo_id=None)
        with patch.object(geo_engine, 'update_geo_from_object', return_value={'revision': 2}) as update:
            self.assertEqual(self.obj.update_geo('geo', 7, 50, expected_revision=1), {'revision': 2})
            update.assert_called_once_with('item::test', 'item', 'geo', 7, 50, expected_revision=1)
        with patch.object(geo_engine, 'get_geo_from_object', return_value={'geo_id': 'geo'}) as get:
            self.assertEqual(self.obj.get_geo('geo'), {'geo_id': 'geo'})
            get.assert_called_once_with('item::test', 'geo')
        with patch.object(geo_engine, 'get_object_geos', return_value=[]) as get_all:
            self.assertEqual(self.obj.get_geos(offset=10, limit=20), [])
            get_all.assert_called_once_with('item::test', offset=10, limit=20)
        with patch.object(geo_engine, 'get_object_nb_geos', return_value=2):
            self.assertEqual(self.obj.get_nb_geos(), 2)
            self.assertTrue(self.obj.is_geo())
        with patch.object(geo_engine, 'remove_geo_from_object', return_value=True) as remove:
            self.assertTrue(self.obj.remove_geo('geo'))
            remove.assert_called_once_with('item::test', 'item', 'geo')
        with patch.object(geo_engine, 'delete_all_geo_from_object', return_value=2) as remove_all:
            self.assertEqual(self.obj.delete_geos(), 2)
            remove_all.assert_called_once_with('item::test', 'item')

    def test_missing_objects_cannot_receive_or_update_coordinates(self):
        self.obj.present = False
        with patch.object(geo_engine, 'add_geo_to_object') as add, patch.object(geo_engine, 'update_geo_from_object') as update:
            with self.assertRaises(ValueError):
                self.obj.add_geo(6, 49)
            with self.assertRaises(ValueError):
                self.obj.update_geo('geo', 6, 49)
        add.assert_not_called()
        update.assert_not_called()

    def test_geo_metadata_is_opt_in_and_identifies_partial_lists(self):
        self.obj.get_geos = Mock(return_value=[{'latitude': 89, 'longitude': 6}] * 100)
        self.obj.get_nb_geos = Mock(return_value=105)
        meta = self.obj.get_default_meta()
        self.assertNotIn('geo', meta)
        self.assertNotIn('geo_count', meta)
        self.obj.get_geos.assert_not_called()
        self.obj.get_nb_geos.assert_not_called()
        meta = self.obj.get_default_meta(options={'geo', 'geo_count'})
        self.assertEqual(meta['geo_count'], 105)
        self.assertEqual(meta['geo']['total'], 105)
        self.assertTrue(meta['geo']['has_more'])
        self.assertEqual(meta['geo']['locations'][0]['latitude'], 89)
        self.obj.get_geos.assert_called_once_with(offset=0, limit=100)
        self.obj.get_nb_geos.assert_called_once_with()

    def test_count_only_metadata_does_not_fetch_locations(self):
        self.obj.get_nb_geos = Mock(return_value=3)
        self.obj.get_geos = Mock()
        self.assertEqual(self.obj.get_default_meta(options={'geo_count'})['geo_count'], 3)
        self.obj.get_geos.assert_not_called()

    def test_empty_geo_metadata_has_no_more_pages(self):
        self.obj.get_nb_geos = Mock(return_value=0)
        self.obj.get_geos = Mock(return_value=[])
        self.assertEqual(self.obj.get_geo_meta(), {'locations': [], 'total': 0, 'offset': 0, 'limit': 100, 'has_more': False})

    def test_shared_metadata_builders_forward_geo_options(self):
        expected = {'locations': [], 'total': 0, 'offset': 0, 'limit': 100, 'has_more': False}
        self.obj.get_geo_meta = Mock(return_value=expected)
        self.obj.get_first_seen = Mock(return_value='20261013')
        self.obj.get_last_seen = Mock(return_value='20261013')
        self.obj.get_nb_seen = Mock(return_value=1)
        for path, name in (('bin/lib/objects/abstract_daterange_object.py', 'AbstractDaterangeObject'), ('bin/lib/objects/abstract_subtype_object.py', 'AbstractSubtypeObject')):
            with self.subTest(builder=name):
                method = load_object_method(path, name, '_get_meta', {})
                self.assertEqual(method(self.obj, options={'geo'})['geo'], expected)

    def test_domain_and_screenshot_metadata_include_geo_when_requested(self):
        expected = {'locations': [{'latitude': 90, 'longitude': 0}], 'total': 1, 'offset': 0, 'limit': 100, 'has_more': False}
        self.obj.get_geo_meta = Mock(return_value=expected)
        self.obj.domain_type = 'onion'
        self.obj.get_first_seen = Mock(return_value='20261013')
        self.obj.get_last_check = Mock(return_value='20261013')
        self.obj.get_tags = Mock(return_value=[])
        self.obj.is_up = Mock(return_value=True)
        for path, name in (('bin/lib/objects/Domains.py', 'Domain'), ('bin/lib/objects/Screenshots.py', 'Screenshot')):
            with self.subTest(object=name):
                self.obj.get_geo_meta.reset_mock()
                method = load_object_method(path, name, 'get_meta', {'get_screenshot_rel_path': lambda value: value})
                self.assertNotIn('geo', method(self.obj))
                self.obj.get_geo_meta.assert_not_called()
                self.assertEqual(method(self.obj, options={'geo'})['geo'], expected)

    def test_all_registered_metadata_paths_support_geo_options(self):
        for obj_type, path, class_name, method in registered_object_methods('get_meta'):
            with self.subTest(object=obj_type):
                calls = [node for node in ast.walk(method) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
                direct = any(node.func.attr == '_add_geo_meta' for node in calls)
                shared = any(node.func.attr in ('get_default_meta', '_get_meta') and any(keyword.arg == 'options' for keyword in node.keywords) for node in calls)
                self.assertTrue(direct or shared, f'{path}:{class_name} omits GEO metadata')

    def test_common_deletion_cleans_geo_before_other_metadata(self):
        stub_object_cleanup(self.obj)
        order = []
        self.obj._delete_metas.side_effect = lambda: order.append('metadata')
        with patch.object(geo_engine, 'delete_all_geo_from_object', side_effect=lambda *args: order.append('geo')):
            self.obj._delete_object()
        self.assertEqual(order, ['geo', 'metadata'])

    def test_geo_failure_stops_common_metadata_deletion(self):
        stub_object_cleanup(self.obj)
        with patch.object(geo_engine, 'delete_all_geo_from_object', side_effect=RedisError('unavailable')):
            with self.assertRaises(RedisError):
                self.obj._delete_object()
        self.obj._delete_metas.assert_not_called()
        self.obj.delete_trackers.assert_not_called()


class KvrocksGeoTests(IsolatedKvrocksTestCase):
    def test_multiple_locations_and_original_precision(self):
        longitude, latitude = 6.131912345678, 49.611612345678
        first = geo_engine.add_geo_to_object('item::example', 'item', longitude, latitude)
        second = geo_engine.add_geo_to_object('item::example', 'item', 2.3522, 48.8566)
        geo = geo_engine.get_geo_from_object('item::example', first)
        self.assertEqual((geo['longitude'], geo['latitude']), (longitude, latitude))
        self.assertEqual(geo['revision'], 1)
        self.assertEqual(uuid.UUID(first).version, 4)
        self.assertNotEqual(first, second)
        self.assertEqual(geo_engine.get_object_nb_geos('item::example'), 2)
        self.assertEqual({entry['geo_id'] for entry in geo_engine.get_object_geos('item::example')}, {first, second})
        self.assertEqual(set(self.db.hgetall(f'geo:observation:{first}')), {'obj_gid', 'longitude', 'latitude', 'created_at', 'updated_at', 'revision'})
        self.assertEqual(self.db.zcard('geo:index:all'), 2)
        self.assertEqual(self.db.zcard('geo:index:type:item'), 2)
        self.assertIsNone(self.db.get('other-namespace'))
        self.assertEqual(self.admin.get('other-namespace'), 'untouched')

    def test_same_coordinates_keep_independent_owners(self):
        first = geo_engine.add_geo_to_object('item::example', 'item', 0, 0)
        second = geo_engine.add_geo_to_object('username:telegram:alice:extra/id', 'username', 0, 0)
        self.assertNotEqual(first, second)
        self.assertEqual(geo_engine.get_geo_object_gid(second), 'username:telegram:alice:extra/id')
        self.assertEqual(self.db.geopos('geo:index:all', first, second)[0], self.db.geopos('geo:index:all', first, second)[1])
        self.assertEqual({entry['geo_id'] for entry in geo_engine.yield_objects_type_geos('username')}, {second})

    def test_polar_coordinates_are_clamped_in_both_indexes(self):
        for latitude in (90, -90, 89, -89, geo_engine.GEO_MAX_LATITUDE, -geo_engine.GEO_MAX_LATITUDE):
            with self.subTest(latitude=latitude):
                geo_id = geo_engine.add_geo_to_object('image::polar', 'image', 6, latitude)
                self.assertEqual(geo_engine.get_geo_from_object('image::polar', geo_id)['latitude'], latitude)
                expected = geo_engine.get_indexed_latitude(latitude)
                for index in ('geo:index:all', 'geo:index:type:image'):
                    self.assertAlmostEqual(self.db.geopos(index, geo_id)[0][1], expected, delta=0.00001)
        for longitude in (-180, 180):
            geo_id = geo_engine.add_geo_to_object('image::polar', 'image', longitude, 90)
            self.assertEqual(geo_engine.get_geo_from_object('image::polar', geo_id)['longitude'], longitude)

    def test_update_preserves_identity_and_order_and_replaces_spatial_position(self):
        geo_id = geo_engine.add_geo_to_object('item::example', 'item', 6.1319, 49.6116)
        before = geo_engine.get_geo_from_object('item::example', geo_id)
        score = self.db.zscore('geo:object:item::example', geo_id)
        updated = geo_engine.update_geo_from_object('item::example', 'item', geo_id, 2.3522, 90, expected_revision=1)
        self.assertEqual(updated['geo_id'], geo_id)
        self.assertEqual(updated['created_at'], before['created_at'])
        self.assertEqual(updated['revision'], 2)
        self.assertEqual(self.db.zscore('geo:object:item::example', geo_id), score)
        self.assertEqual(updated['latitude'], 90)
        self.assertAlmostEqual(self.db.geopos('geo:index:all', geo_id)[0][1], geo_engine.GEO_MAX_LATITUDE, delta=0.00001)
        self.assertEqual(self.db.geosearch('geo:index:all', longitude=6.1319, latitude=49.6116, radius=1, unit='km'), [])
        self.assertEqual(self.db.geosearch('geo:index:all', longitude=2.3522, latitude=geo_engine.GEO_MAX_LATITUDE, radius=1, unit='km'), [geo_id])
        self.assertEqual(geo_engine.update_geo_from_object('item::example', 'item', geo_id, 2.3522, 90, expected_revision=2), updated)
        with self.assertRaises(geo_engine.GeoConflictError):
            geo_engine.update_geo_from_object('item::example', 'item', geo_id, 0, 0, expected_revision=1)
        self.assertEqual(geo_engine.get_geo_from_object('item::example', geo_id), updated)

    def test_wrong_owners_and_id_reuse_cannot_change_records_or_indexes(self):
        geo_id = geo_engine.add_geo_to_object('item::owner', 'item', 6, 49)
        before = geo_engine.get_geo_from_object('item::owner', geo_id)
        operations = (lambda: geo_engine.get_geo_from_object('item::wrong', geo_id),
                      lambda: geo_engine.update_geo_from_object('item::wrong', 'item', geo_id, 0, 0),
                      lambda: geo_engine.remove_geo_from_object('item::wrong', 'item', geo_id),
                      lambda: geo_engine.add_geo_to_object('message::wrong', 'message', 0, 0, geo_id=geo_id))
        for operation in operations:
            with self.assertRaises(geo_engine.GeoConflictError):
                operation()
        self.assertEqual(geo_engine.get_geo_from_object('item::owner', geo_id), before)
        self.assertEqual(self.db.zcard('geo:index:all'), 1)
        self.assertFalse(geo_engine.object_has_geo('item::wrong'))
        self.assertFalse(geo_engine.object_has_geo('message::wrong'))

    def test_remove_and_delete_all_clean_every_index(self):
        first = geo_engine.add_geo_to_object('item::owner', 'item', 6, 49)
        second = geo_engine.add_geo_to_object('item::owner', 'item', 2, 48)
        unrelated = geo_engine.add_geo_to_object('message::other', 'message', 7, 50)
        self.assertTrue(geo_engine.remove_geo_from_object('item::owner', 'item', first))
        self.assertFalse(geo_engine.remove_geo_from_object('item::owner', 'item', first))
        self.assertIsNone(geo_engine.get_geo_from_object('item::owner', first))
        self.assertIsNone(self.db.zscore('geo:index:all', first))
        self.assertIsNone(self.db.zscore('geo:index:type:item', first))
        self.assertEqual(geo_engine.delete_all_geo_from_object('item::owner', 'item'), 1)
        self.assertEqual(geo_engine.delete_all_geo_from_object('item::owner', 'item'), 0)
        self.assertFalse(geo_engine.object_has_geo('item::owner'))
        self.assertIsNone(geo_engine.get_geo_object_gid(second))
        self.assertEqual(self.db.zrange('geo:index:all', 0, -1), [unrelated])

    def test_missing_locations_return_explicit_empty_results(self):
        geo_id = uuid.uuid4().hex
        self.assertEqual(geo_engine.get_object_geos('item::missing'), [])
        self.assertEqual(geo_engine.get_object_nb_geos('item::missing'), 0)
        self.assertIsNone(geo_engine.get_geo_from_object('item::missing', geo_id))
        self.assertIsNone(geo_engine.update_geo_from_object('item::missing', 'item', geo_id, 0, 0))
        self.assertFalse(geo_engine.remove_geo_from_object('item::missing', 'item', geo_id))
        self.assertEqual(geo_engine.delete_all_geo_from_object('item::missing', 'item'), 0)
        self.assertEqual(self.db.dbsize(), 0)

    def test_bounded_listing_uses_creation_order(self):
        geo_ids = []
        for index in range(5):
            with patch.object(geo_engine.time, 'time_ns', return_value=(1000 + index) * 1_000_000):
                geo_ids.append(geo_engine.add_geo_to_object('item::page', 'item', index, index))
        self.assertEqual([geo['geo_id'] for geo in geo_engine.get_object_geos('item::page', offset=1, limit=2)], geo_ids[1:3])
        self.assertEqual(geo_engine.get_object_geos('item::page', offset=5), [])

    def test_incompatible_index_type_is_rejected_before_any_write(self):
        geo_id = uuid.uuid4().hex
        self.db.set('geo:index:all', 'wrong-type')
        with self.assertRaises(geo_engine.GeoStorageError):
            geo_engine.add_geo_to_object('item::example', 'item', 0, 0, geo_id=geo_id)
        self.assertFalse(self.db.exists(f'geo:observation:{geo_id}', 'geo:object:item::example', 'geo:index:type:item'))
        self.assertEqual(self.db.get('geo:index:all'), 'wrong-type')

    def test_wrong_owner_in_bulk_membership_aborts_entire_deletion(self):
        first = geo_engine.add_geo_to_object('item::owner', 'item', 6, 49)
        second = geo_engine.add_geo_to_object('message::other', 'message', 7, 50)
        self.db.zadd('geo:object:item::owner', {second: 0})
        with self.assertRaises(geo_engine.GeoConflictError):
            geo_engine.delete_all_geo_from_object('item::owner', 'item')
        self.assertEqual(geo_engine.get_geo_object_gid(first), 'item::owner')
        self.assertEqual(geo_engine.get_geo_object_gid(second), 'message::other')
        self.assertEqual(self.db.zcard('geo:index:all'), 2)

    def test_bulk_deletion_retries_when_another_location_is_added(self):
        geo_engine.add_geo_to_object('item::owner', 'item', 6, 49)
        original_pipeline = self.db.pipeline
        injected = []

        def concurrent_pipeline(*args, **kwargs):
            pipe = original_pipeline(*args, **kwargs)
            original_execute = pipe.execute

            def execute(*execute_args, **execute_kwargs):
                if not injected:
                    injected.append(True)
                    injected.append(geo_engine.add_geo_to_object('item::owner', 'item', 7, 50))
                return original_execute(*execute_args, **execute_kwargs)

            pipe.execute = execute
            return pipe

        with patch.object(self.db, 'pipeline', side_effect=concurrent_pipeline):
            self.assertEqual(geo_engine.delete_all_geo_from_object('item::owner', 'item'), 2)
        self.assertEqual(self.db.dbsize(), 0)
        self.assertIsNone(geo_engine.get_geo_object_gid(injected[1]))

    def test_update_retries_then_rejects_stale_revision_after_concurrent_edit(self):
        geo_id = geo_engine.add_geo_to_object('item::owner', 'item', 6, 49)
        original_pipeline = self.db.pipeline
        injected = []

        def concurrent_pipeline(*args, **kwargs):
            pipe = original_pipeline(*args, **kwargs)
            original_execute = pipe.execute

            def execute(*execute_args, **execute_kwargs):
                if not injected:
                    injected.append(True)
                    injected.append(geo_engine.update_geo_from_object('item::owner', 'item', geo_id, 7, 50, expected_revision=1))
                return original_execute(*execute_args, **execute_kwargs)

            pipe.execute = execute
            return pipe

        with patch.object(self.db, 'pipeline', side_effect=concurrent_pipeline):
            with self.assertRaises(geo_engine.GeoConflictError):
                geo_engine.update_geo_from_object('item::owner', 'item', geo_id, 0, 0, expected_revision=1)
        self.assertEqual(geo_engine.get_geo_from_object('item::owner', geo_id), injected[1])
        self.assertAlmostEqual(self.db.geopos('geo:index:all', geo_id)[0][1], 50, delta=0.00001)

    def test_every_registered_deletion_path_removes_all_its_locations(self):
        object_class = load_object_class()
        namespace = {'r_object': Mock(), 'image_similarity': Mock(), 'os': SimpleNamespace(remove=Mock()),
                     'IS_MEILISEARCH_ENABLED': False, 'send_message_from_module': Mock()}
        delete_chat = load_object_method('bin/lib/objects/abstract_chat_object.py', 'AbstractChatObject', '_delete_chat', namespace)
        unrelated = geo_engine.add_geo_to_object('message::keep', 'message', 1, 1)
        for obj_type, path, class_name, _ in registered_object_methods('delete'):
            with self.subTest(object=obj_type):
                obj = object_class(obj_type, 'deleted', subtype='fixture')
                obj.present = True
                stub_object_cleanup(obj)
                obj._delete_chat = MethodType(delete_chat, obj)
                obj.get_filename = Mock(return_value='unused-test-file')
                first = obj.add_geo(6, 49)
                second = obj.add_geo(7, 90)
                delete = load_object_method(path, class_name, 'delete', namespace)
                delete(obj)
                self.assertEqual(obj.get_nb_geos(), 0)
                self.assertIsNone(geo_engine.get_geo_object_gid(first))
                self.assertIsNone(geo_engine.get_geo_object_gid(second))
                self.assertIsNone(self.db.zscore('geo:index:all', first))
                self.assertIsNone(self.db.zscore(f'geo:index:type:{obj_type}', second))
                self.assertIsNotNone(geo_engine.get_geo_from_object('message::keep', unrelated))

    def test_object_metadata_returns_original_coordinates_and_correct_count(self):
        obj = load_object_class()('image', 'metadata')
        obj.present = True
        geo_id = obj.add_geo(6.123456789, 90)
        meta = obj.get_default_meta(options={'geo', 'geo_count'})
        self.assertEqual(meta['geo_count'], 1)
        self.assertEqual(meta['geo']['locations'][0]['geo_id'], geo_id)
        self.assertEqual(meta['geo']['locations'][0]['latitude'], 90)
        self.assertFalse(meta['geo']['has_more'])

    def test_repair_audit_reports_missing_and_incorrect_indexes_without_writing(self):
        geo_id = geo_engine.add_geo_to_object('item::repair', 'item', 6, 90)
        record = self.db.hgetall(f'geo:observation:{geo_id}')
        self.db.delete('geo:object:item::repair', 'geo:index:type:item')
        self.db.geoadd('geo:index:all', [10, 10, geo_id])
        report = geo_engine.repair_geo_indexes(owner_exists=lambda gid: True)
        self.assertFalse(report['applied'])
        self.assertEqual(report['missing_references'], 2)
        self.assertEqual(report['incorrect_positions'], 1)
        self.assertEqual(report['reindexed'], 0)
        self.assertEqual(report['error_count'], 0)
        self.assertFalse(self.db.exists('geo:object:item::repair', 'geo:index:type:item'))
        self.assertAlmostEqual(self.db.geopos('geo:index:all', geo_id)[0][1], 10, delta=0.00001)
        self.assertEqual(self.db.hgetall(f'geo:observation:{geo_id}'), record)

    def test_repair_rebuilds_indexes_from_original_coordinates_without_changing_records(self):
        geo_id = geo_engine.add_geo_to_object('item::repair', 'item', 6, -90)
        record = self.db.hgetall(f'geo:observation:{geo_id}')
        self.db.delete('geo:object:item::repair', 'geo:index:type:item')
        self.db.geoadd('geo:index:all', [10, 10, geo_id])
        report = geo_engine.repair_geo_indexes(apply=True, owner_exists=lambda gid: True)
        self.assertEqual(report['reindexed'], 1)
        self.assertEqual(report['error_count'], 0)
        self.assertEqual(self.db.hgetall(f'geo:observation:{geo_id}'), record)
        self.assertEqual(self.db.zscore('geo:object:item::repair', geo_id), int(record['created_at']))
        for index in ('geo:index:all', 'geo:index:type:item'):
            longitude, latitude = self.db.geopos(index, geo_id)[0]
            self.assertAlmostEqual(longitude, 6, delta=0.00001)
            self.assertAlmostEqual(latitude, -geo_engine.GEO_MAX_LATITUDE, delta=0.00001)
        audit = geo_engine.repair_geo_indexes(owner_exists=lambda gid: True)
        for field in ('missing_references', 'incorrect_positions', 'incorrect_order', 'stale_references', 'error_count'):
            self.assertEqual(audit[field], 0)

    def test_repair_removes_dangling_and_wrong_owner_references(self):
        geo_id = geo_engine.add_geo_to_object('item::repair', 'item', 6, 49)
        missing = uuid.uuid4().hex
        self.db.geoadd('geo:index:all', [10, 10, missing])
        self.db.geoadd('geo:index:type:item', [10, 10, missing])
        self.db.zadd('geo:object:item::repair', {missing: 0})
        self.db.zadd('geo:object:message::wrong', {geo_id: 0})
        self.db.geoadd('geo:index:type:message', [6, 49, geo_id])
        report = geo_engine.repair_geo_indexes(apply=True, owner_exists=lambda gid: True)
        self.assertEqual(report['removed_references'], 5)
        self.assertEqual(report['error_count'], 0)
        self.assertEqual(geo_engine.get_object_nb_geos('item::repair'), 1)
        self.assertEqual(self.db.zrange('geo:index:all', 0, -1), [geo_id])
        self.assertFalse(self.db.exists('geo:object:message::wrong', 'geo:index:type:message'))

    def test_orphan_records_require_explicit_removal_and_an_owner_check(self):
        geo_id = geo_engine.add_geo_to_object('item::gone', 'item', 6, 49)
        audit = geo_engine.repair_geo_indexes(owner_exists=lambda gid: False, remove_orphans=True)
        self.assertEqual(audit['orphans'], 1)
        self.assertEqual(audit['removed_orphans'], 0)
        self.assertEqual(self.db.zcard('geo:index:all'), 1)
        report = geo_engine.repair_geo_indexes(apply=True, owner_exists=lambda gid: False)
        self.assertEqual(report['removed_references'], 3)
        self.assertEqual(report['removed_orphans'], 0)
        self.assertIsNotNone(geo_engine.get_geo_object_gid(geo_id))
        with self.assertRaises(ValueError):
            geo_engine.repair_geo_indexes(apply=True, remove_orphans=True)
        report = geo_engine.repair_geo_indexes(apply=True, owner_exists=lambda gid: False, remove_orphans=True)
        self.assertEqual(report['removed_orphans'], 1)
        self.assertEqual(self.db.dbsize(), 0)

    def test_repair_restores_object_creation_order(self):
        geo_id = geo_engine.add_geo_to_object('item::repair', 'item', 6, 49)
        created_at = geo_engine.get_geo_from_object('item::repair', geo_id)['created_at']
        self.db.zadd('geo:object:item::repair', {geo_id: 0})
        report = geo_engine.repair_geo_indexes(apply=True)
        self.assertEqual(report['incorrect_order'], 1)
        self.assertEqual(self.db.zscore('geo:object:item::repair', geo_id), created_at)

    def test_repair_reports_invalid_records_and_keeps_them_for_review(self):
        for field, value in (('latitude', 'nan'), ('revision', '0'), ('created_at', '-1')):
            with self.subTest(field=field):
                self.db.flushdb()
                geo_id = geo_engine.add_geo_to_object('item::invalid', 'item', 6, 49)
                self.db.hset(f'geo:observation:{geo_id}', field, value)
                before = self.db.hgetall(f'geo:observation:{geo_id}')
                report = geo_engine.repair_geo_indexes(apply=True, owner_exists=lambda gid: False, remove_orphans=True)
                self.assertGreater(report['error_count'], 0)
                self.assertEqual(report['removed_orphans'], 0)
                self.assertEqual(self.db.hgetall(f'geo:observation:{geo_id}'), before)

    def test_repair_does_not_overwrite_incompatible_storage_types(self):
        geo_id = geo_engine.add_geo_to_object('item::repair', 'item', 6, 49)
        record = self.db.hgetall(f'geo:observation:{geo_id}')
        self.db.delete('geo:index:all')
        self.db.set('geo:index:all', 'incompatible')
        report = geo_engine.repair_geo_indexes(apply=True)
        self.assertGreater(report['error_count'], 0)
        self.assertEqual(self.db.get('geo:index:all'), 'incompatible')
        self.assertEqual(self.db.hgetall(f'geo:observation:{geo_id}'), record)

    def test_repair_retries_concurrent_updates_using_the_latest_coordinates(self):
        geo_id = geo_engine.add_geo_to_object('item::repair', 'item', 6, 49)
        original_pipeline = self.db.pipeline
        injected = []

        def concurrent_pipeline(*args, **kwargs):
            pipe = original_pipeline(*args, **kwargs)
            original_execute = pipe.execute

            def execute(*execute_args, **execute_kwargs):
                if not injected:
                    injected.append(True)
                    injected.append(geo_engine.update_geo_from_object('item::repair', 'item', geo_id, 7, 90))
                return original_execute(*execute_args, **execute_kwargs)

            pipe.execute = execute
            return pipe

        with patch.object(self.db, 'pipeline', side_effect=concurrent_pipeline):
            report = geo_engine.repair_geo_indexes(apply=True)
        self.assertEqual(report['error_count'], 0)
        self.assertEqual(geo_engine.get_geo_from_object('item::repair', geo_id), injected[1])
        self.assertAlmostEqual(self.db.geopos('geo:index:all', geo_id)[0][1], geo_engine.GEO_MAX_LATITUDE, delta=0.00001)


if __name__ == '__main__':
    unittest.main()

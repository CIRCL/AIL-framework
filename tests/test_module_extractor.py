#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import types
import unittest
import importlib
from unittest.mock import patch


if 'AIL_BIN' not in os.environ:
    os.environ['AIL_BIN'] = os.path.join(os.getcwd(), 'bin')
sys.path.append(os.environ['AIL_BIN'])

# Stub optional runtime dependencies so module_extractor can be imported in CI-lite envs.
if 'yara' not in sys.modules:
    sys.modules['yara'] = types.SimpleNamespace(CALLBACK_CONTINUE=0, CALLBACK_MATCHES=1, Error=Exception)

stub_ail_users = types.ModuleType('lib.ail_users')
stub_ail_users.get_user_org = lambda _user_id: 'org-1'
sys.modules.setdefault('lib.ail_users', stub_ail_users)

stub_objects_pkg = types.ModuleType('lib.objects')
stub_ail_objects = types.SimpleNamespace(get_object=lambda *_args, **_kwargs: None)
stub_titles = types.ModuleType('lib.objects.Titles')


class _Title:
    def __init__(self, value):
        self._value = value

    def get_content(self):
        return self._value


stub_titles.Title = _Title
stub_objects_pkg.ail_objects = stub_ail_objects
sys.modules.setdefault('lib.objects', stub_objects_pkg)
sys.modules.setdefault('lib.objects.Titles', stub_titles)

stub_exceptions = types.ModuleType('lib.exceptions')
stub_exceptions.TimeoutException = RuntimeError
sys.modules.setdefault('lib.exceptions', stub_exceptions)

stub_corr = types.ModuleType('lib.correlations_engine')
stub_corr.get_correlation_by_correl_type = lambda *_args, **_kwargs: []
sys.modules.setdefault('lib.correlations_engine', stub_corr)

stub_regex = types.ModuleType('lib.regex_helper')
stub_regex.generate_redis_cache_key = lambda _name: 'extractor-test-key'
stub_regex.regex_finditer = lambda *_args, **_kwargs: []
stub_regex.regex_escape = lambda value: value
sys.modules.setdefault('lib.regex_helper', stub_regex)


class _FakeRedis:
    def get(self, _key):
        return None

    def set(self, _key, _value):
        return True

    def expire(self, _key, _ttl):
        return True

    def smembers(self, _key):
        return []

    def delete(self, _key):
        return True

    def sadd(self, _key, _value):
        return True


class _FakeConfigLoader:
    def get_redis_conn(self, _name):
        return _FakeRedis()


stub_cfg = types.ModuleType('lib.ConfigLoader')
stub_cfg.ConfigLoader = _FakeConfigLoader
sys.modules.setdefault('lib.ConfigLoader', stub_cfg)

stub_tracker = types.ModuleType('lib.Tracker')
stub_tracker.Tracker = lambda uuid: None
stub_tracker.RetroHunt = lambda uuid: None
stub_tracker.get_obj_trackers = lambda *_args, **_kwargs: []
stub_tracker.get_obj_retro_hunts = lambda *_args, **_kwargs: []
stub_tracker.get_tracked_typosquatting_domains = lambda *_args, **_kwargs: []
stub_tracker.is_tracker = lambda _uuid: True
sys.modules.setdefault('lib.Tracker', stub_tracker)


def _stub_module_class(module_name, class_name):
    mod = types.ModuleType(module_name)

    class _M:
        def __init__(self, queue=False):
            pass

        def extract(self, obj, content, tag):
            return []

    _M.__name__ = class_name
    setattr(mod, class_name, _M)
    return mod


sys.modules.setdefault('modules.CreditCards', _stub_module_class('modules.CreditCards', 'CreditCards'))
sys.modules.setdefault('modules.Iban', _stub_module_class('modules.Iban', 'Iban'))
sys.modules.setdefault('modules.Mail', _stub_module_class('modules.Mail', 'Mail'))
sys.modules.setdefault('modules.Onion', _stub_module_class('modules.Onion', 'Onion'))
sys.modules.setdefault('modules.Phone', _stub_module_class('modules.Phone', 'Phone'))
sys.modules.setdefault('modules.Tools', _stub_module_class('modules.Tools', 'Tools'))
sys.modules['modules.Tools'].Tools.get_tools = lambda self: []

module_extractor = importlib.import_module('lib.module_extractor')


class FakeObj:
    type = 'item'

    def __init__(self):
        self.id = 'obj-id'

    def exists(self):
        return True

    def get_global_id(self):
        return 'item::obj-id'

    def get_subtype(self, r_str=False):
        return ''

    def get_tags(self):
        return ['infoleak:automatic-detection="mail"']

    def get_content(self):
        return 'safe content'


class FakeTracker:
    def __init__(self, uuid):
        self.uuid = uuid

    def check_level(self, user_org, user_id):
        return True

    def get_type(self):
        return 'regex'

    def get_tracked(self):
        return '(a+)+$'


class FakeModule:
    def extract(self, obj, content, tag):
        return [[10, 14, 'mail', f'tag:{tag}']]


class TestModuleExtractor(unittest.TestCase):

    def test_regex_timeout_is_routed_through_regex_helper(self):
        calls = []

        def fake_regex_finditer(r_key, regex, item_id, content, max_time=30):
            calls.append({'regex': regex, 'max_time': max_time, 'item_id': item_id})
            return []

        with patch.object(module_extractor.Tracker, 'Tracker', FakeTracker):
            with patch.object(module_extractor.regex_helper, 'regex_finditer', side_effect=fake_regex_finditer):
                module_extractor._get_trackers_match(
                    ['tracker-1'], 'org-1', 'user-1', 'item::obj-id', 'aaaaaaaaaaaaaaaa!'
                )

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['regex'], '(a+)+$')
        self.assertLessEqual(calls[0]['max_time'], module_extractor.REGEX_MAX_SECONDS)

    def test_global_timeout_returns_partial_results(self):
        fake_obj = FakeObj()
        call_count = {'count': 0}

        def fake_deadline_exceeded(_start_time, max_seconds=60):
            call_count['count'] += 1
            # allow object lookup + tracker pass, then stop module/correlation loops
            return call_count['count'] >= 3

        with patch.object(module_extractor.ail_objects, 'get_object', return_value=fake_obj):
            with patch.object(module_extractor, 'get_user_org', return_value='org-1'):
                with patch.object(module_extractor, 'get_tracker_match', return_value=[[0, 4, 'seed', 'tracker:t1']]):
                    with patch.object(module_extractor, 'deadline_exceeded', side_effect=fake_deadline_exceeded):
                        result = module_extractor.extract('user-1', 'item', '', 'obj-id', content='safe content')

        self.assertEqual(result, [(0, 4, 'seed', [('tracker:t1', 'seed')])])

    def test_extract_regression_normal_flow(self):
        fake_obj = FakeObj()
        fake_module = FakeModule()
        with patch.object(module_extractor.ail_objects, 'get_object', return_value=fake_obj):
            with patch.object(module_extractor, 'get_user_org', return_value='org-1'):
                with patch.object(module_extractor, 'get_tracker_match', return_value=[[0, 4, 'seed', 'tracker:t1']]):
                    with patch.object(module_extractor, 'MODULES', {'infoleak:automatic-detection="mail"': fake_module}):
                        with patch.object(module_extractor, 'CORRELATION_TO_EXTRACT', {'item': []}):
                            result = module_extractor.extract('user-1', 'item', '', 'obj-id', content='safe content')

        self.assertEqual(result, [
            (0, 4, 'seed', [('tracker:t1', 'seed')]),
            (10, 14, 'mail', [('tag:infoleak:automatic-detection="mail"', 'mail')]),
        ])


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import importlib.util
import types
from unittest.mock import patch

AIL_HOME = os.environ.get('AIL_HOME')
sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################

if 'html2text' not in sys.modules:
    html2text_module = types.ModuleType('html2text')
    class _HTML2Text:
        ignore_links = False
        ignore_images = False
        def handle(self, content):
            return content
    html2text_module.HTML2Text = _HTML2Text
    sys.modules['html2text'] = html2text_module

if 'gcld3' not in sys.modules:
    gcld3_module = types.ModuleType('gcld3')
    class _Identifier:
        def __init__(self, *args, **kwargs):
            pass
        def FindTopNMostFreqLangs(self, content, num_langs=1):
            return []
    gcld3_module.NNetLanguageIdentifier = _Identifier
    sys.modules['gcld3'] = gcld3_module

if 'picolang' not in sys.modules:
    picolang_module = types.ModuleType('picolang')
    detector_module = types.ModuleType('picolang.detector')
    detector_module.detect = lambda content: ('en', 1.0)
    sys.modules['picolang'] = picolang_module
    sys.modules['picolang.detector'] = detector_module

if 'libretranslatepy' not in sys.modules:
    lt_module = types.ModuleType('libretranslatepy')
    class _LT:
        def __init__(self, *args, **kwargs):
            pass
    lt_module.LibreTranslateAPI = _LT
    sys.modules['libretranslatepy'] = lt_module

if 'pycountry' not in sys.modules:
    pycountry_module = types.ModuleType('pycountry')

    class _Collection(list):
        def get(self, **kwargs):
            for entry in self:
                if all(getattr(entry, k, None) == v for k, v in kwargs.items()):
                    return entry
            return None

    def _entry(**kwargs):
        return types.SimpleNamespace(**kwargs)

    pycountry_module.languages = _Collection([
        _entry(alpha_2='en', alpha_3='eng', name='English'),
        _entry(alpha_2='fr', alpha_3='fra', name='French'),
        _entry(alpha_2='de', alpha_3='deu', name='German'),
        _entry(alpha_2='sr', alpha_3='srp', name='Serbian'),
        _entry(alpha_2='zh', alpha_3='zho', name='Chinese'),
        _entry(alpha_2='pt', alpha_3='por', name='Portuguese'),
    ])
    pycountry_module.scripts = _Collection([
        _entry(alpha_4='Hans'),
        _entry(alpha_4='Hant'),
        _entry(alpha_4='Cyrl'),
    ])
    pycountry_module.countries = _Collection([
        _entry(alpha_2='US', numeric='840'),
        _entry(alpha_2='BR', numeric='076'),
        _entry(alpha_2='RS', numeric='688'),
    ])
    sys.modules['pycountry'] = pycountry_module

from lib import Language

SCRIPT_PATH = os.path.join(AIL_HOME, 'update', 'v6.8', 'migrate_message_languages_to_bcp47.py')
spec = importlib.util.spec_from_file_location('migrate_message_languages_to_bcp47', SCRIPT_PATH)
migrate_message_languages_to_bcp47 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrate_message_languages_to_bcp47)


class TestLanguageBCP47(unittest.TestCase):

    def test_valid_bcp47_normalization(self):
        self.assertEqual(Language.normalize_bcp47_tag('en'), 'en')
        self.assertEqual(Language.normalize_bcp47_tag('EN-us'), 'en-US')
        self.assertEqual(Language.normalize_bcp47_tag('zh-hant'), 'zh-Hant')
        self.assertEqual(Language.normalize_bcp47_tag('sr-cyrl-rs'), 'sr-Cyrl-RS')

    def test_iso6393_to_bcp47_migration(self):
        self.assertEqual(Language.iso639_3_to_bcp47_primary('eng'), 'en')
        self.assertEqual(Language.iso639_3_to_bcp47_primary('fra'), 'fr')
        self.assertEqual(Language.iso639_3_to_bcp47_primary('deu'), 'de')
        self.assertEqual(Language.iso639_3_to_bcp47_primary('srp'), 'sr')
        self.assertEqual(Language.iso639_3_to_bcp47_primary('zho'), 'zh')

    def test_already_valid_bcp47(self):
        self.assertTrue(Language.is_valid_bcp47_tag('pt-BR'))
        self.assertEqual(Language.normalize_bcp47_tag('pt-BR'), 'pt-BR')

    def test_invalid_bcp47(self):
        self.assertIsNone(Language.normalize_bcp47_tag('english'))
        self.assertIsNone(Language.normalize_bcp47_tag('en-XYZ'))

    def test_get_all_languages_is_bcp47_keyed(self):
        languages = Language.get_all_languages()
        self.assertEqual(languages['en'], 'English')
        self.assertEqual(languages['fr'], 'French')
        self.assertEqual(languages['sh'], 'Serbo-Croatian')
        self.assertNotIn('eng', languages)


class FakeRedis:
    def scan_iter(self, match=None):
        return ['obj:lang:message:1', 'obj:lang:message:2']


class FakeMessage:
    _languages = {
        '1': {'eng', 'fr'},
        '2': {'???', 'en-US'}
    }

    def __init__(self, message_id):
        self.message_id = message_id

    def get_languages(self):
        return set(self._languages[self.message_id])

    def get_global_id(self):
        return f'message::{self.message_id}'

    def remove_language(self, language):
        self._languages[self.message_id].discard(language)

    def add_language(self, language):
        self._languages[self.message_id].add(language)


class TestMigrationScript(unittest.TestCase):

    @patch.object(migrate_message_languages_to_bcp47.Messages, 'Message', FakeMessage)
    def test_migrate_message_languages(self):
        counters = migrate_message_languages_to_bcp47.migrate_message_languages(FakeRedis(), dry_run=False)
        self.assertEqual(FakeMessage._languages['1'], {'en', 'fr'})
        self.assertEqual(FakeMessage._languages['2'], {'en-US', '???'})
        self.assertEqual(counters['migrated_iso639_3'], 1)
        self.assertEqual(counters['already_valid_bcp47'], 2)
        self.assertEqual(counters['skipped_invalid'], 1)


if __name__ == '__main__':
    unittest.main()

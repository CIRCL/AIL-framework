#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('AIL_BIN', str(REPO_ROOT / 'bin'))
sys.path.append(str(REPO_ROOT / 'bin'))

from lib import retro_hunt_markdown


class TestRetroHuntMarkdown(unittest.TestCase):

    def test_build_match_excerpts_merges_overlapping_context_windows(self):
        content = '\n'.join([f'line {i}' for i in range(1, 16)])
        start_one = content.index('line 6')
        end_one = start_one + len('line 6')
        start_two = content.index('line 9')
        end_two = start_two + len('line 9')

        excerpts = retro_hunt_markdown.build_match_excerpts(
            content,
            [(start_one, end_one, 'line 6'), (start_two, end_two, 'line 9')],
            context_lines=5,
        )

        self.assertEqual(len(excerpts), 1)
        self.assertIn('<mark>line 6</mark>', excerpts[0]['rendered'])
        self.assertIn('<mark>line 9</mark>', excerpts[0]['rendered'])
        self.assertEqual(excerpts[0]['line_label'], 'Lines 1-14')

    def test_build_retro_hunt_markdown_contains_metadata_and_object_sections(self):
        retro_hunt_meta = {
            'uuid': 'hunt-uuid',
            'name': 'My Retro Hunt',
            'description': 'hunt description',
            'filters': {'item': {}, 'message': {}},
        }
        objects = [{
            'meta': {
                'type': 'item',
                'id': 'item-1',
                'subtype': '',
            },
            'date_label': '2025-01-01',
            'infoleak_tags': ['infoleak:automatic-detection="credit-card"'],
            'excerpts': [{
                'line_label': 'Lines 1-3',
                'rendered': '<pre>hello <mark>world</mark></pre>'
            }],
        }]

        markdown = retro_hunt_markdown.build_retro_hunt_markdown(retro_hunt_meta, 'rule test { condition: true }', objects)

        self.assertIn('# Retro Hunt Export - My Retro Hunt', markdown)
        self.assertIn('**Targeted object types:** item, message', markdown)
        self.assertIn('```yara', markdown)
        self.assertIn('### Object 1: item / N/A / item-1', markdown)
        self.assertIn('**Infoleak taxonomy tags:** infoleak:automatic-detection="credit-card"', markdown)
        self.assertIn('<pre>hello <mark>world</mark></pre>', markdown)


if __name__ == '__main__':
    unittest.main()

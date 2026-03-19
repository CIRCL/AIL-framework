#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import html
import re
from typing import List, Tuple


def get_targeted_object_types(filters):
    if filters:
        return sorted(filters.keys())
    from lib import ail_core
    return sorted(ail_core.get_objects_retro_hunted())


def get_infoleak_taxonomy_tags(tags):
    return sorted([tag for tag in (tags or []) if tag.startswith('infoleak:')])


def format_object_date(meta):
    first_seen = meta.get('first_seen')
    last_seen = meta.get('last_seen')
    if first_seen or last_seen:
        if first_seen and last_seen:
            return f'{first_seen} / {last_seen}'
        return first_seen or last_seen
    return meta.get('full_date') or meta.get('date') or meta.get('last_full_date') or 'Unknown'


def normalize_content(content):
    if content is None:
        return ''
    if isinstance(content, bytes):
        return content.decode('utf-8', errors='replace')
    return str(content)


def _compute_line_ranges(content: str, matches: List[Tuple[int, int, str]], context_lines: int = 5):
    if not content:
        return []

    lines = content.splitlines(keepends=True)
    if not lines:
        lines = ['']

    line_starts = []
    cursor = 0
    for line in lines:
        line_starts.append(cursor)
        cursor += len(line)
    line_starts.append(len(content))

    def find_line(offset):
        if offset <= 0:
            return 0
        if offset >= len(content):
            return max(len(lines) - 1, 0)
        for i in range(len(lines)):
            if line_starts[i] <= offset < line_starts[i + 1]:
                return i
        return max(len(lines) - 1, 0)

    spans = []
    for idx, match in enumerate(matches):
        start, end = int(match[0]), int(match[1])
        if end < start:
            end = start
        start_line = max(find_line(start) - context_lines, 0)
        end_line = min(find_line(max(end - 1, start)) + context_lines, len(lines) - 1)
        spans.append({'start_line': start_line, 'end_line': end_line, 'match_indexes': [idx]})

    if not spans:
        return []

    merged = [spans[0]]
    for span in spans[1:]:
        current = merged[-1]
        if span['start_line'] <= current['end_line'] + 1:
            current['end_line'] = max(current['end_line'], span['end_line'])
            current['match_indexes'].extend(span['match_indexes'])
        else:
            merged.append(span)

    for span in merged:
        span['start_char'] = line_starts[span['start_line']]
        span['end_char'] = line_starts[span['end_line'] + 1]
        span['line_label'] = f"Lines {span['start_line'] + 1}-{span['end_line'] + 1}"
    return merged


def _render_highlighted_pre(excerpt, excerpt_matches):
    fragments = []
    cursor = 0
    for start, end, _value in excerpt_matches:
        rel_start = max(start - excerpt['start_char'], 0)
        rel_end = min(end - excerpt['start_char'], len(excerpt['text']))
        if rel_start > cursor:
            fragments.append(html.escape(excerpt['text'][cursor:rel_start]))
        matched_text = excerpt['text'][rel_start:rel_end]
        if matched_text:
            fragments.append(f'<mark>{html.escape(matched_text)}</mark>')
        cursor = max(cursor, rel_end)
    if cursor < len(excerpt['text']):
        fragments.append(html.escape(excerpt['text'][cursor:]))
    return '<pre>\n' + ''.join(fragments) + '\n</pre>'


def build_match_excerpts(content, matches, context_lines=5):
    normalized_content = normalize_content(content)
    normalized_matches = [tuple(match[:3]) for match in (matches or [])]
    excerpts = []
    for span in _compute_line_ranges(normalized_content, normalized_matches, context_lines=context_lines):
        excerpt_matches = []
        for idx in span['match_indexes']:
            start, end, value = normalized_matches[idx]
            excerpt_matches.append((int(start), int(end), value))
        excerpt = {
            'line_label': span['line_label'],
            'text': normalized_content[span['start_char']:span['end_char']],
            'start_char': span['start_char'],
            'end_char': span['end_char'],
            'matches': excerpt_matches,
        }
        excerpt['rendered'] = _render_highlighted_pre(excerpt, excerpt_matches)
        excerpts.append(excerpt)
    return excerpts


def _sanitize_filename(value):
    sanitized = re.sub(r'[^A-Za-z0-9._-]+', '-', value.strip()).strip('-')
    return sanitized or 'retro-hunt'


def build_retro_hunt_markdown(retro_hunt_meta, rule_content, objects):
    targeted_objects = ', '.join(get_targeted_object_types(retro_hunt_meta.get('filters')))
    lines = [
        f"# Retro Hunt Export - {retro_hunt_meta.get('name', 'Unnamed Retro Hunt')}",
        '',
        '## Description',
        '',
        f"- **Retro hunt name:** {retro_hunt_meta.get('name', 'Unknown')}",
        f"- **Retro hunt description:** {retro_hunt_meta.get('description') or 'No description provided'}",
        f"- **Targeted object types:** {targeted_objects}",
        '',
        '## YARA Rule',
        '',
        '```yara',
        rule_content or '',
        '```',
        '',
        '## Results',
        ''
    ]

    if not objects:
        lines.extend(['No matched objects were available for export.', ''])

    for index, obj in enumerate(objects, start=1):
        subtype = obj['meta'].get('subtype') or 'N/A'
        infoleak_tags = obj.get('infoleak_tags') or []
        if obj['meta'].get('type'):
            object_label = f"{obj['meta']['type']} / {subtype} / {obj['meta']['id']}"
        else:
            object_label = obj['meta']['id']
        lines.extend([
            f"### Object {index}: {object_label}",
            '',
            f"- **Object ID:** {obj['meta']['id']}",
            f"- **Subtype:** {subtype}",
            f"- **Infoleak taxonomy tags:** {', '.join(infoleak_tags) if infoleak_tags else 'None'}",
            f"- **Date(s):** {obj['date_label']}",
            ''
        ])

        if obj.get('excerpts'):
            for excerpt_index, excerpt in enumerate(obj['excerpts'], start=1):
                lines.extend([
                    f"#### Match Excerpt {excerpt_index}",
                    '',
                    f"_{excerpt['line_label']}_",
                    '',
                    excerpt['rendered'],
                    ''
                ])
        else:
            lines.extend([
                '#### Match Excerpts',
                '',
                '_No textual excerpt could be generated for this object._',
                ''
            ])

    return '\n'.join(lines).strip() + '\n'


def get_retro_hunt_export_filename(retro_hunt_meta):
    name = retro_hunt_meta.get('name', 'retro-hunt')
    uuid = retro_hunt_meta.get('uuid', 'export')
    return f"{_sanitize_filename(name)}-{uuid}.md"

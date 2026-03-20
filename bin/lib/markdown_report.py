#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import html
import re

def _normalize_sort_date(value):
    if value is None:
        return None
    normalized = re.sub(r'[^0-9]', '', str(value))
    if len(normalized) >= 8:
        return normalized[:8]
    return None


def get_object_sort_key(obj):
    meta = obj.get('meta') or {}
    sort_date = (_normalize_sort_date(meta.get('first_seen')) or
                 _normalize_sort_date(meta.get('last_seen')) or
                 _normalize_sort_date(meta.get('last_full_date')))
    object_type = meta.get('type') or ''
    object_subtype = meta.get('subtype') or ''
    object_id = meta.get('id') or ''
    missing_date = sort_date is None
    return (missing_date, sort_date or '', object_type, object_subtype, object_id)


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
    return meta.get('full_date') or meta.get('date') or meta.get('last_full_date') or None


def normalize_content(content):
    if content is None:
        return ''
    if isinstance(content, bytes):
        return content.decode('utf-8', errors='replace')
    return str(content)


def _compute_line_ranges(content, matches, context_lines=5):
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


def _build_markdown_document(url_root, lines, objects):
    objects = sorted(objects, key=get_object_sort_key)
    lines.extend(['## Results', ''])

    if not objects:
        lines.extend(['No matched objects were available for export.', ''])

    for index, obj in enumerate(objects, start=1):
        subtype = obj['meta'].get('subtype') or ''
        infoleak_tags = obj.get('infoleak_tags') or []
        if len(obj['meta']['id']) > 20:
            if obj['meta']['type'] == 'item':
                s_obj_id = obj['meta']['id'].split('/')
                s_obj_id = f"{s_obj_id[0]} {s_obj_id[-1]}"
            elif obj['meta']['type'] == 'message':
                s_obj_id = obj['meta']['id'].split('/', 1)[-1]
            else:
                s_obj_id = obj['meta']['id'][30:]
        else:
            s_obj_id = obj['meta']['id']
        object_label = f"{obj['meta']['type']} {subtype} [{s_obj_id}]({url_root}{obj['meta']['link']})"

        lines.extend([
            f"### Object {index}: {object_label}",
            '',
        ])
        if obj['meta'].get('protocol'):
            lines.append(f"- **Platform:** {obj['meta']['protocol']}")
        if infoleak_tags:
            lines.append(f"- **Tags:** {', '.join(infoleak_tags)}")
        if obj['date_label']:
            lines.append(f"- **Date:** {obj['date_label']}")
        lines.append('')

        if obj.get('excerpts'):
            for excerpt_index, excerpt in enumerate(obj['excerpts'], start=1):
                lines.extend([
                    f"#### Match Preview {excerpt_index}",
                    f"_{excerpt['line_label']}_",
                    '',
                    excerpt['rendered'],
                    ''
                ])
        else:
            lines.extend([
                '#### Match Preview',
                '_No textual excerpt could be generated for this object._',
                ''
            ])
    return '\n'.join(lines).strip() + '\n'


def build_retro_hunt_markdown(url_root, retro_hunt_meta, rule_content, objects):
    targeted_objects = ', '.join(get_targeted_object_types(retro_hunt_meta.get('filters')))
    lines = [
        f"# <img src=\"https://ail-project.org/assets/img/ail-project-medium.png\" alt=\"AIL Project\" width=\"120\"> Retro Hunt - {retro_hunt_meta.get('name', '')}",
        '',
        '## Details',
        '',
        f"- **Name:** {retro_hunt_meta.get('name', 'Unknown')}",
        f"- **UUID:** {retro_hunt_meta.get('uuid', '')}"
    ]
    if retro_hunt_meta.get('description'):
        lines.append(f"- **Description:** {retro_hunt_meta.get('description') or 'No description provided'}")
    lines.extend([
        f"- **Targeted object types:** {targeted_objects}",
        '',
        '### YARA Rule',
        '',
        '```yara',
        rule_content or '',
        '```',
        '',
    ])
    return _build_markdown_document(url_root, lines, objects)


def build_tracker_markdown(url_root, tracker_meta, rule_content, objects, filter_obj_types=None, date_from=None, date_to=None):
    filter_obj_types = sorted(filter_obj_types or [])
    targeted_objects = ', '.join(filter_obj_types) if filter_obj_types else 'All tracked object types'
    lines = [
        f"# <img src=\"https://ail-project.org/assets/img/ail-project-medium.png\" alt=\"AIL Project\" width=\"120\"> Tracker Export - {tracker_meta.get('description') or tracker_meta.get('uuid', '')}",
        '',
        '## Details',
        '',
        f"- **UUID:** {tracker_meta.get('uuid', '')}",
        f"- **Tracker type:** {tracker_meta.get('type', 'Unknown')}",
        f"- **Tracked:** {tracker_meta.get('tracked', 'Unknown')}",
        f"- **Targeted object types:** {targeted_objects}",
    ]
    if tracker_meta.get('description'):
        lines.append(f"- **Description:** {tracker_meta.get('description')}")

    lines.append('')
    lines.append('### Match Information')
    if date_from or date_to:
        if date_from and date_to:
            date_from = f"{date_from[0:4]}/{date_from[4:6]}/{date_from[6:8]}"
            date_to = f"{date_to[0:4]}/{date_to[4:6]}/{date_to[6:8]}"
        elif date_from:
            date_from = f"{date_from[0:4]}/{date_from[4:6]}/{date_from[6:8]}"
        else:
            date_to = f"{date_to[0:4]}/{date_to[4:6]}/{date_to[6:8]}"
        lines.append(f"- **Match date range:** {date_from or 'N/A'} - {date_to or 'N/A'}")
    if tracker_meta.get('first_seen'):
        lines.append(f"- **First seen:** {tracker_meta.get('first_seen')[0:4]}/{tracker_meta.get('first_seen')[4:6]}/{tracker_meta.get('first_seen')[6:8]}")
    if tracker_meta.get('last_seen'):
        lines.append(f"- **Last seen:** {tracker_meta.get('last_seen')[0:4]}/{tracker_meta.get('last_seen')[4:6]}/{tracker_meta.get('last_seen')[6:8]}")
    lines.append('')

    if rule_content:
        lines.extend(['### YARA Rule', '```yara', rule_content, '```', ''])

    return _build_markdown_document(url_root, lines, objects)


def get_retro_hunt_export_filename(retro_hunt_meta):
    name = retro_hunt_meta.get('name', 'retro-hunt')
    uuid = retro_hunt_meta.get('uuid', 'export')
    return f"retrohunt_{_sanitize_filename(name)}-{uuid}.md"


def get_tracker_export_filename(tracker_meta):
    uuid = tracker_meta.get('uuid', 'export')
    return f"tracker_{uuid}.md"

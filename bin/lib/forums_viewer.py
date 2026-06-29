#!/usr/bin/python3

"""
Forums Viewer
===================

"""
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ail_core import unpack_obj_global_id
# from lib.ConfigLoader import ConfigLoader
from lib.objects import Forums
from lib.objects import Subforums
from lib.objects import ForumThreads
from lib.objects import Posts
from lib.objects import UsersAccount
from lib.objects import ail_objects
from lib import crawlers
from lib import Language
from lib.crawlers import Cookiejar

# config_loader = ConfigLoader()
# config_loader = None

_FORUM_OPTIONS = {'forum_type', 'info', 'name', 'url', 'nb_subforums', 'nb_orphan_subforums'}
_SUBFORUM_OPTIONS = {'info', 'url', 'nb_subforums', 'nb_threads'}
_THREAD_OPTIONS = {'name', 'info', 'url', 'flags', 'nb_posts'}
_POST_OPTIONS = {'content', 'language', 'link', 'state', 'timestamp', 'translation', 'user-account'}
_FORUM_CRAWL_WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

def update_account_cookies_local_storage(account, cookies, local_storage):
    cookiejar_uuid = account.get_cookiejar_uuid()
    if not cookiejar_uuid:
        return False
    cookiejar = Cookiejar(cookiejar_uuid)
    if local_storage:
        cookiejar.set_cookies(cookies)
        cookiejar.set_local_storage(local_storage)
    return True

def _split_lines(value):
    if not value:
        return []
    if isinstance(value, (list, set, tuple)):
        return [v.strip() for v in value if v and str(v).strip()]
    return [line.strip() for line in str(value).replace(',', '\n').splitlines() if line.strip()]

def _minute_to_time(value):
    value = int(value or 0)
    if value >= 1440:
        return '23:59'
    hour = value // 60
    minute = value % 60
    return f'{hour}:{minute:02d}'

def _active_time_to_ui(active_time):
    active_time_ui = {}
    for weekday in _FORUM_CRAWL_WEEKDAYS:
        ranges = []
        for start, end in (active_time or {}).get(weekday) or []:
            ranges.append({'start': _minute_to_time(start), 'end': _minute_to_time(end)})
        active_time_ui[weekday] = {'enabled': bool(ranges), 'ranges': ranges or [{'start': '0:00', 'end': '23:59'}]}
    return active_time_ui

def _get_form_list(data, field):
    value = data.getlist(field) if hasattr(data, 'getlist') else data.get(field, [])
    if isinstance(value, str):
        return [value]
    return value or []

# TODO Check overlapping
def _active_time_from_form(data):
    weekdays = _get_form_list(data, 'active_time_days')
    if not weekdays:
        return None
    active_time = {weekday: [] for weekday in _FORUM_CRAWL_WEEKDAYS}
    for weekday in weekdays:
        if weekday not in active_time:
            continue
        starts = _get_form_list(data, f'active_time_start_{weekday}')
        ends = _get_form_list(data, f'active_time_end_{weekday}')
        for start, end in zip(starts, ends):
            start = (start or '').strip()
            end = (end or '').strip()
            if start and end:
                active_time[weekday].append([start, end])
    return active_time


def create_forum(data):
    forum_id = (data.get('forum_id') or data.get('id')).strip()
    forum_type = (data.get('forum_type', 'default')).strip()
    name = (data.get('name', '')).strip()
    url = (data.get('url', '')).strip()
    info = (data.get('info', '')).strip()
    if not forum_id:
        return {"status": "error", "error": "Missing forum_id"}, 400
    if not forum_type:
        return {"status": "error", "error": "Missing forum_type"}, 400
    forum = Forums.Forum(forum_id)
    if forum.exists():
        return {"status": "error", "error": "Forum already exists", "forum_id": forum_id}, 409
    forum.create(forum_type, name=name, url=url, info=info)
    return forum.get_meta(_FORUM_OPTIONS, flask_context=True), 200

def get_forum_crawl_management(forum_id):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "error": "Unknown forum"}, 404
    config = forum.get_crawl_config()
    accounts = []
    for account_id in sorted(config.get('accounts', [])):
        account_meta = forum.get_crawl_account(account_id).get_meta()
        if account_meta.get('active_time'):
            account_meta['active_time_ui'] = _active_time_to_ui(account_meta.get('active_time'))
        else:
            account_meta['active_time_ui'] = None
        accounts.append(account_meta)
    return {
        'forum': forum.get_meta(options=_FORUM_OPTIONS, flask_context=True),
        'config': config,
        'accounts': accounts,
    }, 200

def update_forum_crawl_config(forum_id, data):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "error": "Unknown forum"}, 404
    config = {
        'proxy': data.get('proxy'),
        'delta_subforum_refresh': data.get('delta_subforum_refresh'),
        'delta_thread_refresh': data.get('delta_thread_refresh'),
        'default_referer': data.get('default_referer'),
        'timeout': data.get('timeout'),
        'subforums_excluded': _split_lines(data.get('subforums_excluded')),
        'subforums_to_crawl': _split_lines(data.get('subforums_to_crawl')),
    }
    if data.get('enabled') == 'on':
        config['enabled'] = 1
    else:
        config['enabled'] = 0
    if data.get('javascript') == 'on':
        config['javascript'] = 1
    else:
        config['javascript'] = 0
    meta = forum.set_crawl_config(config)
    forum.refresh_accounts_availability()
    return meta, 200

def _account_form_to_meta(data, meta=None):
    if not meta:
        meta = {}
    if data.get('enabled') == 'on':
        meta['enabled'] = 1
    else:
        meta['enabled'] = 0
    meta['status'] = data.get('status', 'need_manual_login')
    meta['cookiejar_uuid'] = data.get('cookiejar_uuid', None)
    meta['random_time_between_page'] = data.get('random_time_between_page', None)
    meta['subforums_to_crawl'] = _split_lines(data.get('subforums_to_crawl'))
    if data.get('active_time_mode') == 'limited':
        meta['active_time'] = _active_time_from_form(data)
    else:
        meta['active_time'] = None
    return meta

def save_forum_crawl_account(forum_id, account_id, data):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "error": "Unknown forum"}, 404
    if not account_id:
        return {"status": "error", "error": "Missing account_id"}, 400
    if account_id in forum.get_crawl_accounts():
        account = forum.get_crawl_account(account_id)
        account.set_meta(_account_form_to_meta(data, meta=account.get_meta()))
    else:
        account = forum.add_crawl_account(account_id, _account_form_to_meta(data))
    forum.refresh_account_availability(account_id)
    return account.get_meta(), 200

def delete_forum_crawl_account(forum_id, account_id):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "error": "Unknown forum"}, 404
    if account_id not in forum.get_crawl_accounts():
        return {"status": "error", "error": "Unknown account"}, 404
    account = forum.get_crawl_account(account_id)
    account.clear_current_crawl()
    forum.remove_crawl_account(account_id)
    account.delete_meta()
    return {'forum_id': forum_id, 'account_id': account_id}, 200


def api_reactivate_errored_forum_crawl_account(forum_id, account_id):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "error": "Unknown forum"}, 404
    account = forum.get_crawl_account(account_id)
    if not account.exists():
        return {"status": "error", "error": "Unknown account"}, 404
    if account.get_status() != 'error':
        return {"status": "error", "error": "Account is not in error status"}, 400
    account.clear_current_crawl()
    account.clear_error()
    forum.refresh_account_availability(account_id)
    return account.get_meta(), 200

def api_set_forum_account_local_storage(user_org, user_id, data):
    if not isinstance(data, dict):
        return {'status': 'error', 'error': 'Invalid JSON body'}, 400
    forum_id = data.get('forum_id')
    account_id = data.get('account_id')
    local_storage = data.get('local_storage')
    if not isinstance(local_storage, dict):
        return {'status': 'error', 'error': 'local_storage must be a JSON object'}, 400
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {'status': 'error', 'error': 'Unknown forum'}, 404
    if not forum.exists_account(account_id):
        return {'status': 'error', 'error': 'Unknown account'}, 404
    account = forum.get_crawl_account(account_id)
    cookiejar_uuid = account.get_cookiejar_uuid()
    if not cookiejar_uuid:
        cookiejar_uuid = crawlers.create_cookiejar(user_org, user_id, f'Forum {forum_id} account {account_id} browser state', 0, None)
        account.set_cookiejar_uuid(cookiejar_uuid)
    cookiejar = Cookiejar(cookiejar_uuid)
    if not cookiejar.exists():
        return {'status': 'error', 'error': 'unknown cookiejar uuid', 'cookiejar_uuid': cookiejar_uuid}, 404
    cookiejar.set_cookies(local_storage.get('cookies', []))
    cookiejar.set_local_storage(local_storage)
    account.set_status('waiting')
    forum.refresh_account_availability(account_id)
    return {'forum_id': forum_id, 'account_id': account_id, 'cookiejar_uuid': cookiejar_uuid}, 200

def _subforum_meta(subforum, flask_context=True):
    meta = subforum.get_meta(_SUBFORUM_OPTIONS, flask_context=flask_context)
    meta['name'] = meta.get('name') or meta.get('id')
    return meta

def _thread_meta(thread, flask_context=True):
    meta = thread.get_meta(_THREAD_OPTIONS, flask_context=flask_context)
    meta['name'] = meta.get('name') or meta.get('id')
    return meta

def _children_meta(parent, child_type):
    children = []
    for child_global_id in parent.get_childrens():
        obj_type, subtype, obj_id = unpack_obj_global_id(child_global_id)
        if obj_type != child_type:
            continue
        obj = ail_objects.get_object(obj_type, subtype, obj_id)
        if not obj.exists():
            continue
        if obj_type == 'subforum':
            children.append(_subforum_meta(obj))
        elif obj_type == 'forum-thread':
            children.append(_thread_meta(obj))
    # TODO CHANGE SORT
    return sorted(children, key=lambda m: ((m.get('name') or m.get('title') or m.get('id')).lower(), m.get('id')))


def get_forums():
    """Return metadata for all imported Forum objects."""
    forums = []
    for forum_id in Forums.get_forums():
        forum = Forums.Forum(forum_id)
        if forum.exists():
            forums.append(forum.get_meta(_FORUM_OPTIONS, flask_context=True))
    return sorted(forums, key=lambda m: ((m.get('name') or m.get('id')).lower(), m.get('id')))



def get_forums_crawl_status():
    """Return crawler status summaries for all imported Forum objects."""
    forums = []
    for forum_id in Forums.get_forums():
        forum = Forums.Forum(forum_id)
        if not forum.exists():
            continue
        meta = forum.get_meta(_FORUM_OPTIONS, flask_context=True)
        status = forum.get_crawl_status(sample_size=0)
        meta['crawler_status'] = status
        forums.append(meta)
    return sorted(forums, key=lambda m: ((m.get('name') or m.get('id')).lower(), m.get('id')))

def api_get_forum_crawl_status(forum_id):
    """Return read-only crawler status for one Forum object."""
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "reason": "Unknown forum"}, 404
    config = forum.get_crawl_config()
    return {
        'forum': forum.get_meta(_FORUM_OPTIONS, flask_context=True),
        'config': {
            'enabled': config.get('enabled'),
            'javascript': config.get('javascript'),
            'proxy': config.get('proxy'),
            'default_referer': config.get('default_referer'),
            'timeout': config.get('timeout'),
            'delta_subforum_refresh': config.get('delta_subforum_refresh'),
            'delta_thread_refresh': config.get('delta_thread_refresh'),
        },
        'status': forum.get_crawl_status(sample_size=5),
    }, 200


def api_get_forum_crawl_queue(forum_id, sample_size=50):
    """Return read-only crawler queue details for one Forum object."""
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "reason": "Unknown forum"}, 404
    try:
        sample_size = max(int(sample_size), 1)
    except (TypeError, ValueError):
        sample_size = 50
    return {
        'forum': forum.get_meta(_FORUM_OPTIONS, flask_context=True),
        'queue': forum.get_crawl_queue_status(sample_size=sample_size),
        'sample_size': sample_size,
    }, 200


def enqueue_forum_root_crawl(forum_id):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "reason": "Unknown forum"}, 404
    url = forum.get_url()
    if not url:
        return {"status": "error", "reason": "Forum URL is missing"}, 400
    item = {
        'crawl_key': f'forum:{forum_id}',
        'type': 'forum',
        'id': forum_id,
        'url': url,
        'referer': forum.get_default_referer(),
        'crawl_mode': 'discovery',
    }
    queued, reason = forum.enqueue_crawl_item(item, 10)
    if not queued:
        status_code = 409 if reason == 'already_queued' else 400
        return {'status': 'error', 'reason': reason, 'forum_id': forum_id, 'crawl_key': item['crawl_key']}, status_code
    return {'forum_id': forum_id, 'crawl_key': item['crawl_key'], 'url': url}, 200

def purge_forum_crawl_queue(forum_id):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "reason": "Unknown forum"}, 404
    return {
        'forum_id': forum_id,
        'deleted': forum.purge_crawl_queue(),
    }, 200

def get_breadcrumb_for_object(obj):
    """Return parent breadcrumb entries from Forum to the given object."""
    breadcrumb = []
    current = obj
    seen = set()
    while current:
        global_id = current.get_global_id()
        if global_id in seen:
            break
        seen.add(global_id)
        if current.type == 'forum':
            meta = current.get_meta(_FORUM_OPTIONS, flask_context=True)
            breadcrumb.append(meta)
            break
        elif current.type == 'subforum':
            meta = _subforum_meta(current)
        elif current.type == 'forum-thread':
            meta = _thread_meta(current)
        else:
            meta = current.get_default_meta()
        breadcrumb.append(meta)
        parent_gid = current.get_parent()
        if not parent_gid:
            break
        current = ail_objects.get_object(*unpack_obj_global_id(parent_gid))
    return list(reversed(breadcrumb))

#### API ####

def api_get_forum(forum_id):
    """Return forum metadata with root and orphan subforums."""
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "reason": "Unknown forum"}, 404

    orphan_subforums = []
    orphan_gids = set(forum.get_orphan_subforums())
    for orphan_gid in orphan_gids:
        obj_type, obj_subtype, obj_id = unpack_obj_global_id(orphan_gid)
        if obj_type != 'subforum':
            continue
        subforum = Subforums.Subforum(obj_id, obj_subtype)
        if subforum.exists():
            meta = _subforum_meta(subforum)
            meta['orphan'] = True
            orphan_subforums.append(meta)

    return {
        'forum': forum.get_meta(_FORUM_OPTIONS, flask_context=True),
        'subforums': _children_meta(forum, 'subforum'),
        'orphan_subforums': sorted(orphan_subforums, key=lambda m: ((m.get('name') or m.get('id')).lower(), m.get('id'))),
    }, 200

def api_get_subforum(subtype, subforum_id):
    """Return subforum metadata with child subforums and forum threads."""
    subforum = Subforums.Subforum(subforum_id, subtype)
    if not subforum.exists():
        return {"status": "error", "reason": "Unknown forum subforum"}, 404
    return {
        'subforum': _subforum_meta(subforum),
        'breadcrumb': get_breadcrumb_for_object(subforum),
        'subforums': _children_meta(subforum, 'subforum'),
        'threads': _children_meta(subforum, 'forum-thread'),
    }, 200

def api_get_forum_thread(subtype, thread_id, page=1, nb=50, translation_target=None):
    """Return thread metadata and timestamp-ordered posts."""
    thread = ForumThreads.ForumThread(thread_id, subtype)
    if not thread.exists():
        return {"status": "error", "reason": "Unknown forum thread"}, 404
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    if page < 1:
        page = 1
    try:
        nb = int(50)
    except (TypeError, ValueError):
        nb = 50
    if page < 1:
        nb = 50
    posts, pagination, tags = thread.get_posts(page=page, nb=nb, options=_POST_OPTIONS, translation_target=translation_target)
    return {
        'thread': _thread_meta(thread),
        'breadcrumb': get_breadcrumb_for_object(thread),
        'posts': posts,
        'pagination': pagination,
        'tags': tags,
    }, 200



def api_get_post(post_id, translation_target=None):
    post = Posts.Post(post_id)
    if not post.exists():
        return {"status": "error", "reason": "Unknown post"}, 404
    return post.get_meta(_POST_OPTIONS, translation_target=translation_target, flask_context=True), 200

def api_post_detect_language(post_id):
    post = Posts.Post(post_id)
    if not post.exists():
        return {"status": "error", "reason": "Unknown post"}, 404
    lang = post.detect_language()
    return {"language": lang}, 200

def api_manually_translate_post(post_id, source, translation_target, translation):
    post = Posts.Post(post_id)
    if not post.exists():
        return {"status": "error", "reason": "Unknown post"}, 404
    if translation and len(translation) > 200000:
        return {"status": "error", "reason": "Max Size reached"}, 400
    all_languages = Language.get_all_languages()
    if source not in all_languages:
        return {"status": "error", "reason": "Unknown source Language"}, 400
    post_language = post.get_language()
    if post_language != source:
        post.edit_language(post_language, source)
    if translation:
        if translation_target not in all_languages:
            return {"status": "error", "reason": "Unknown target Language"}, 400
        post.set_translation(translation_target, translation)
    return None, 200

def api_get_subforum_last_thread_post(forum_id, subforum_id, thread_id):
    subforum = Subforums.Subforum(subforum_id, forum_id)
    if not subforum.exists():
        return {"status": "error", "reason": "Unknown subforum"}, 404
    return subforum.get_thread_last_post_timestamp(thread_id), 200


if __name__ == '__main__':
    pass

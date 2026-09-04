#!/usr/bin/python3

"""
Forums Viewer
===================

"""
import os
import sys
import time
import magic
from urllib.parse import urlsplit, urlunsplit

from forum_extractor import list_forum_types

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
from lib.objects import Images
from lib.objects import ail_objects
from lib import crawlers
from lib import Language
from packages import Date
from lib.crawlers import Cookiejar

# config_loader = ConfigLoader()
# config_loader = None

_FORUM_OPTIONS = {'banner', 'forum_type', 'info', 'name', 'url', 'nb_subforums', 'nb_orphan_subforums', 'svg_icon'}
_SUBFORUM_OPTIONS = {'info', 'url', 'nb_subforums', 'nb_threads'}
_THREAD_OPTIONS = {'name', 'info', 'url', 'flags', 'nb_posts'}
_POST_OPTIONS = {'content', 'images', 'language', 'link', 'reactions', 'state', 'timestamp', 'translation', 'user-account'}
_FORUM_CRAWL_WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


def _normalize_forum_domain(value):
    value = (value or '').strip().lower()
    if not value:
        return None
    parsed = urlsplit(value if '://' in value else f'//{value}')
    try:
        port = parsed.port
    except ValueError:
        return None
    if (
            not parsed.hostname
            or parsed.username
            or parsed.password
            or port is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in ('', '/')
    ):
        return None
    return parsed.hostname.lower()


def apply_forum_current_domain(url, current_domain):
    if not url:
        return url
    parsed = urlsplit(url)
    domain = current_domain or parsed.hostname
    if not domain:
        return url
    scheme = 'http' if domain.endswith('.onion') else parsed.scheme
    if not current_domain and scheme == parsed.scheme:
        return url
    return urlunsplit((scheme, current_domain or parsed.netloc, parsed.path, parsed.query, parsed.fragment))

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


def update_forum_banner(forum_id, banner_file):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "error": "Unknown forum"}, 404
    if not banner_file or not banner_file.filename:
        return {"status": "error", "error": "Missing banner image"}, 400
    content = banner_file.read()
    if not content:
        return {"status": "error", "error": "Empty banner image"}, 400
    mime = magic.from_buffer(content, mime=True)
    if not mime or not mime.startswith('image/'):
        return {"status": "error", "error": "Banner must be an image"}, 400
    image = Images.create(content, size_limit=5000000)
    if not image:
        return {"status": "error", "error": "Banner image is too large"}, 400
    forum.set_banner(image.id)
    return forum.get_meta(_FORUM_OPTIONS, flask_context=True), 200

def delete_forum_banner(forum_id):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "error": "Unknown forum"}, 404
    forum.delete_banner()
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
        'parser_types': sorted(list_forum_types()),
    }, 200

def update_forum_crawl_config(forum_id, data):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "error": "Unknown forum"}, 404
    current_domain_input = data.get('current_domain')
    current_domain = _normalize_forum_domain(current_domain_input)
    if current_domain_input and not current_domain:
        return {"status": "error", "error": "Invalid current forum domain"}, 400
    forum_type = None
    if 'forum_type' in data:
        forum_type = (data.get('forum_type') or '').strip()
        if forum_type not in list_forum_types():
            return {"status": "error", "error": "Invalid forum parser type"}, 400
    config = {
        'current_domain': current_domain,
        'proxy': data.get('proxy'),
        'delta_forum_structure_refresh': data.get('delta_forum_structure_refresh'),
        'delta_subforum_threads_refresh': data.get('delta_subforum_threads_refresh'),
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
    if current_domain and forum.get_url():
        forum.set_url(apply_forum_current_domain(forum.get_url(), current_domain))
    meta = forum.set_crawl_config(config)
    if forum_type:
        forum.set_forum_type(forum_type)
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
    random_time_between_page = data.get('random_time_between_page')
    if random_time_between_page in (None, ''):
        meta['random_time_between_page'] = None
    else:
        try:
            random_time_between_page = int(random_time_between_page)
        except (TypeError, ValueError) as exc:
            raise ValueError('random_time_between_page must be a positive integer or zero') from exc
        if random_time_between_page < 0:
            raise ValueError('random_time_between_page must be a positive integer or zero')
        meta['random_time_between_page'] = random_time_between_page
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
    try:
        if account_id in forum.get_crawl_accounts():
            account = forum.get_crawl_account(account_id)
            account.set_meta(_account_form_to_meta(data, meta=account.get_meta()))
        else:
            account = forum.add_crawl_account(account_id, _account_form_to_meta(data))
    except ValueError as exc:
        return {'status': 'error', 'error': str(exc)}, 400
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
    crawlers.delete_forum_error_screenshot(forum_id, account_id)
    crawlers.delete_forum_error_html(forum_id, account_id)
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
    crawl_key = account.get_current_crawl_key()
    if crawl_key:
        forum.fail_crawl_item(crawl_key, error='manual_reactivate')
    account.clear_current_crawl()
    account.clear_error()
    crawlers.delete_forum_error_screenshot(forum_id, account_id)
    crawlers.delete_forum_error_html(forum_id, account_id)
    account.clear_last_error_screenshot_metadata()
    account.clear_error_html_metadata()
    forum.refresh_account_availability(account_id)
    return account.get_meta(), 200


def api_purge_forum_account_current_inflight_crawl(forum_id, account_id):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "error": "Unknown forum"}, 404
    account = forum.get_crawl_account(account_id)
    if not account.exists():
        return {'status': 'error', 'error': 'unknown_account'}, 404
    crawl_key = account.get_current_crawl_key()
    if not crawl_key:
        return {'status': 'error', 'error': 'missing_current_crawl'}, 400
    inflight = forum.get_inflight_crawl_item(crawl_key)
    if not inflight:
        return {'status': 'error', 'error': 'current_crawl_not_inflight', 'crawl_key': crawl_key}, 400
    forum.purge_account_current_inflight_crawl(account, crawl_key)
    return account_id, 200

def api_resend_forum_account_current_inflight_crawl(forum_id, account_id):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "error": "Unknown forum"}, 404
    account = forum.get_crawl_account(account_id)
    if not account.exists():
        return {'status': 'error', 'error': 'unknown_account'}, 404
    crawl_key = account.get_current_crawl_key()
    if not crawl_key:
        return {'status': 'error', 'error': 'missing_current_crawl'}, 400
    item = forum.get_crawl_item(crawl_key)
    if not item:
        return {'status': 'error', 'error': 'missing crawl_key', 'crawl_key': crawl_key}, 400
    inflight = forum.get_inflight_crawl_item(crawl_key)
    if not inflight:
        return {'status': 'error', 'error': 'current_crawl_not_inflight', 'crawl_key': crawl_key}, 400
    valid, reason = forum.validate_crawl_item(item)
    if not valid:
        return False, {'status': 'error', 'error': reason, 'crawl_key': crawl_key}
    forum.resend_account_current_inflight_crawl(account, crawl_key)
    crawlers.remove_running_forum_crawler_account(forum.id, account.id)
    return account_id, 200

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
    return sorted(children, key=lambda m: ((m.get('name') or m.get('title') or m.get('id')).lower(), m.get('id')))


def _subforum_threads_meta(subforum):
    threads = []
    thread_ids = set()

    for thread_id, last_post_timestamp in subforum.get_threads_by_last_post():
        thread = ForumThreads.ForumThread(thread_id, subforum.subtype)
        if not thread.exists():
            continue
        meta = _thread_meta(thread)
        meta['last_post_timestamp'] = int(last_post_timestamp)
        meta['last_post_date'] = Date.get_utc_datetime_from_timestamp(last_post_timestamp)
        threads.append(meta)
        thread_ids.add(thread_id)

    # Threads without posts are not present in the last-post zset. Keep them visible
    # after active threads, using the same stable alphabetical ordering as before.
    inactive_threads = []
    for thread_id in subforum.get_threads():
        if thread_id in thread_ids:
            continue
        thread = ForumThreads.ForumThread(thread_id, subforum.subtype)
        if not thread.exists():
            continue
        meta = _thread_meta(thread)
        meta['last_post_timestamp'] = 0
        meta['last_post_date'] = None
        inactive_threads.append(meta)

    return threads + sorted(
        inactive_threads,
        key=lambda m: ((m.get('name') or m.get('title') or m.get('id')).lower(), m.get('id')),
    )


def _get_user_account_posts_sorted(user_account):
    posts = []
    for pid in user_account.get_posts():
        _, post_id = pid.split(':', 1)
        post = Posts.Post(post_id)
        timestamp = post.get_timestamp()
        if timestamp and post.exists():
            posts.append((post, float(timestamp)))
    return sorted(posts, key=lambda post_item: post_item[1], reverse=True)


def _paginate_items(items, page=1, nb=50):
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    try:
        nb = int(nb)
    except (TypeError, ValueError):
        nb = 50
    if page < 1:
        page = 1
    if nb < 1:
        nb = 50
    total = len(items)
    nb_pages = int(total / nb)
    if total and total % nb:
        nb_pages += 1
    if not nb_pages:
        nb_pages = 1
    if page > nb_pages:
        page = nb_pages
    start = (page - 1) * nb
    end = min(start + nb, total)
    return items[start:end], {'nb': nb, 'page': page, 'nb_pages': nb_pages, 'total': total, 'nb_first': start + 1 if total else 0, 'nb_last': end}


def _posts_to_date_dict(post_items, translation_target=None):
    posts_by_date = {}
    for post, timestamp in post_items:
        meta = post.get_meta(_POST_OPTIONS, translation_target=translation_target, flask_context=True)
        date_day = Date.get_utc_date_from_timestamp(timestamp, separator='/')
        posts_by_date.setdefault(date_day, []).append(meta)
    return posts_by_date


def get_user_account_threads_meta(user_account):
    threads = []
    for thread_str in user_account.get_forum_threads():
        thread_subtype, thread_id = thread_str.split(':', 1)
        thread = ForumThreads.ForumThread(thread_id, thread_subtype)
        thread_meta = _thread_meta(thread) if thread.exists() else {'type': 'forum-thread', 'subtype': thread_subtype, 'id': thread_id}
        user_thread_posts = user_account.get_correlation_iter_obj(thread, 'post')
        thread_meta['nb_posts'] = len(user_thread_posts)
        first_post_timestamp = None
        last_post_timestamp = None
        for post_id in user_thread_posts:
            timestamp = Posts.Post(post_id).get_timestamp()
            if not timestamp:
                continue
            timestamp = float(timestamp)
            first_post_timestamp = timestamp if first_post_timestamp is None else min(first_post_timestamp, timestamp)
            last_post_timestamp = timestamp if last_post_timestamp is None else max(last_post_timestamp, timestamp)
        thread_meta['first_post_timestamp'] = first_post_timestamp or 0
        thread_meta['last_post_timestamp'] = last_post_timestamp or 0
        if first_post_timestamp:
            thread_meta['first_post_date'] = Date.get_utc_datetime_from_timestamp(first_post_timestamp)
        else:
            thread_meta['first_post_date'] = None
        if last_post_timestamp:
            thread_meta['last_post_date'] = Date.get_utc_datetime_from_timestamp(last_post_timestamp)
        else:
            thread_meta['last_post_date'] = None
        threads.append(thread_meta)
    return sorted(threads, key=lambda thread: thread['last_post_timestamp'], reverse=True)


def get_user_account_nb_all_week_posts(user_account):
    week = {day: {hour: 0 for hour in range(24)} for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
    for post_gid in user_account.get_posts():
        _, post_id = post_gid.split(':', 1)
        timestamp = Posts.Post(post_id).get_timestamp()
        if not timestamp:
            continue
        weekday, hour = Date.get_utc_weekday_hour_from_timestamp(timestamp)
        week[weekday][hour] += 1
    stats = []
    for nb_day, day in enumerate(week):
        for hour in week[day]:
            stats.append({'date': day, 'day': nb_day, 'hour': hour, 'count': week[day][hour]})
    return stats


def get_user_account_nb_year_posts(user_account, year):
    nb_year = {}
    nb_max = 0
    start = Date.convert_str_date_to_epoch(f'{year}0101')
    end = Date.convert_str_date_to_epoch_end(f'{year}1231')
    for post_gid in user_account.get_posts():
        _, post_id = post_gid.split(':', 1)
        timestamp = Posts.Post(post_id).get_timestamp()
        if not timestamp:
            continue
        timestamp = int(float(timestamp))
        if start <= timestamp <= end:
            date = Date.get_utc_date_from_timestamp(timestamp, separator='-')
            nb_year[date] = nb_year.get(date, 0) + 1
            nb_max = max(nb_max, nb_year[date])
    return nb_max, nb_year


def api_get_user_account(user_id, forum_id, translation_target=None):
    user_account = UsersAccount.UserAccount(user_id, forum_id)
    if not user_account.exists():
        return {"status": "error", "reason": "Unknown user-account"}, 404
    meta = user_account.get_meta({'forums', 'icon', 'info', 'translation', 'username', 'usernames', 'username_meta', 'years', 'nb_posts'}, translation_target=translation_target)
    forum = Forums.Forum(forum_id)
    meta['forum'] = forum.get_meta(_FORUM_OPTIONS, flask_context=True) if forum.exists() else None
    meta['threads'] = get_user_account_threads_meta(user_account)
    return meta, 200


def api_get_user_account_posts(user_id, forum_id, page=1, nb=50, translation_target=None):
    user_account = UsersAccount.UserAccount(user_id, forum_id)
    if not user_account.exists():
        return {"status": "error", "reason": "Unknown user-account"}, 404
    post_items, pagination = _paginate_items(_get_user_account_posts_sorted(user_account), page=page, nb=nb)
    meta = user_account.get_meta({'icon', 'info', 'translation', 'username', 'usernames', 'username_meta'}, translation_target=translation_target)
    forum = Forums.Forum(forum_id)
    meta['forum'] = forum.get_meta(_FORUM_OPTIONS, flask_context=True) if forum.exists() else None
    return {'user-account': meta, 'posts': _posts_to_date_dict(post_items, translation_target=translation_target), 'pagination': pagination}, 200


def api_get_user_account_nb_all_week_posts(user_id, forum_id):
    user_account = UsersAccount.UserAccount(user_id, forum_id)
    if not user_account.exists():
        return {"status": "error", "reason": "Unknown user-account"}, 404
    return get_user_account_nb_all_week_posts(user_account), 200


def api_get_user_account_nb_year_posts(user_id, forum_id, year):
    user_account = UsersAccount.UserAccount(user_id, forum_id)
    if not user_account.exists():
        return {"status": "error", "reason": "Unknown user-account"}, 404
    if not year or year == 'null':
        years = user_account.get_years()
        year = years[-1] if years else int(Date.get_current_year())
    else:
        year = int(year)
    nb_max, nb = get_user_account_nb_year_posts(user_account, year)
    return {'max': nb_max, 'year': year, 'nb': [[date, nb[date]] for date in nb]}, 200


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


def _get_forum_refresh_schedule(delta, next_check, now):
    delta = int(delta or 0)
    if delta <= 0:
        return {'state': 'disabled', 'next_check': None, 'next_check_date': None}
    if next_check is None:
        return {'state': 'not_scheduled', 'next_check': None, 'next_check_date': None}
    next_check = int(next_check)
    return {
        'state': 'due' if next_check <= now else 'waiting',
        'next_check': next_check,
        'next_check_date': Date.get_utc_datetime_from_timestamp(next_check),
    }


def api_get_forum_crawl_status(forum_id):
    """Return read-only crawler status for one Forum object."""
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "reason": "Unknown forum"}, 404
    config = forum.get_crawl_config()
    now = int(time.time())
    return {
        'forum': forum.get_meta(_FORUM_OPTIONS, flask_context=True),
        'config': {
            'enabled': config.get('enabled'),
            'javascript': config.get('javascript'),
            'proxy': config.get('proxy'),
            'default_referer': config.get('default_referer'),
            'current_domain': config.get('current_domain'),
            'timeout': config.get('timeout'),
            'delta_forum_structure_refresh': config.get('delta_forum_structure_refresh'),
            'delta_subforum_threads_refresh': config.get('delta_subforum_threads_refresh'),
        },
        'refresh_schedule': {
            'forum_structure': _get_forum_refresh_schedule(
                config.get('delta_forum_structure_refresh'),
                crawlers.get_forum_structure_refresh_check(forum_id),
                now,
            ),
            'subforum_threads': _get_forum_refresh_schedule(
                config.get('delta_subforum_threads_refresh'),
                crawlers.get_forum_thread_refresh_check(forum_id),
                now,
            ),
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

def remove_forum_pending_crawl_item(forum_id, crawl_key):
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return {"status": "error", "reason": "Unknown forum"}, 404
    removed = forum.remove_pending_crawl_item(crawl_key)
    if not removed:
        return {'status': 'error', 'reason': 'not_pending'}, 404
    return {'forum_id': forum_id, 'crawl_key': crawl_key}, 200

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
        'threads': _subforum_threads_meta(subforum),
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


def api_enqueue_forum_thread_crawl(subtype, thread_id, priority=100):
    """Queue a full thread recrawl from page one with an elevated priority."""
    thread = ForumThreads.ForumThread(thread_id, subtype)
    if not thread.exists():
        return {'status': 'error', 'error': 'unknown_forum_thread'}, 404
    forum = Forums.Forum(subtype)
    if not forum.exists():
        return {'status': 'error', 'error': 'unknown_forum'}, 404
    url = thread.get_url()
    if not url:
        return {'status': 'error', 'error': 'missing_thread_url'}, 400
    parent_gid = thread.get_parent()
    if not parent_gid:
        return {'status': 'error', 'error': 'missing_thread_parent'}, 400
    try:
        parent_type, parent_subtype, parent_id = unpack_obj_global_id(parent_gid)
    except (TypeError, ValueError):
        return {'status': 'error', 'error': 'invalid_thread_parent'}, 400
    if parent_type != 'subforum' or parent_subtype != subtype or not parent_id:
        return {'status': 'error', 'error': 'invalid_thread_parent'}, 400
    task = {
        'crawl_key': f'forum-thread:{thread.id}:page:1',
        'type': 'forum-thread',
        'id': str(thread.id),
        'parent': {'type': 'subforum', 'id': parent_id},
        'page': 1,
        'url': url,
        'referer': forum.get_default_referer(),
        'crawl_mode': 'thread_import',
    }
    allowed, reason = forum.forum_allows_crawl_item(task)
    if not allowed:
        return {'status': 'error', 'error': reason}, 400
    queued, reason = forum.enqueue_crawl_item(task, int(priority))
    if not queued:
        status_code = 409 if reason == 'already_queued' else 400
        return {
            'status': 'error',
            'error': reason or 'unable_to_queue_thread',
            'crawl_key': task['crawl_key'],
        }, status_code
    return {
        'status': 'success',
        'forum_id': forum.id,
        'thread_id': str(thread.id),
        'crawl_key': task['crawl_key'],
        'priority': int(priority),
    }, 200


def api_update_forum_thread_url(subtype, thread_id, url):
    thread = ForumThreads.ForumThread(thread_id, subtype)
    if not thread.exists():
        return {'status': 'error', 'error': 'unknown_forum_thread'}, 404
    url = (url or '').strip()
    parsed = urlsplit(url)
    if (
            parsed.scheme not in {'http', 'https'}
            or not parsed.hostname
            or parsed.username
            or parsed.password
    ):
        return {'status': 'error', 'error': 'invalid_thread_url'}, 400
    thread.set_url(url)
    return {
        'status': 'success',
        'subtype': subtype,
        'thread_id': str(thread.id),
        'url': url,
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

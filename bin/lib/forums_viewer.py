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
from lib.crawlers import Cookiejar

# config_loader = ConfigLoader()
# config_loader = None

_FORUM_OPTIONS = {'forum_type', 'info', 'name', 'url', 'nb_subforums', 'nb_orphan_subforums'}
_SUBFORUM_OPTIONS = {'info', 'url', 'nb_subforums', 'nb_threads'}
_THREAD_OPTIONS = {'title', 'info', 'url', 'flags', 'nb_posts'}
_POST_OPTIONS = {'content', 'link', 'state', 'timestamp', 'user-account'}

def update_account_local_storage(account, local_storage):
    cookiejar_uuid = account.get_cookiejar_uuid()
    if not cookiejar_uuid:
        return False
    cookiejar = Cookiejar(cookiejar_uuid)
    if local_storage:
        cookiejar.set_local_storage(local_storage)
    return True


def _subforum_meta(subforum, flask_context=True):
    meta = subforum.get_meta(_SUBFORUM_OPTIONS, flask_context=flask_context)
    meta['title'] = meta.get('name') or meta.get('id')
    return meta

def _thread_meta(thread, flask_context=True):
    meta = thread.get_meta(_THREAD_OPTIONS, flask_context=flask_context)
    meta['name'] = meta.get('title') or meta.get('id')
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

def api_get_forum_thread(subtype, thread_id, page=1, nb=50):
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
    posts, pagination, tags = thread.get_posts(page=page, nb=nb, options=_POST_OPTIONS)
    return {
        'thread': _thread_meta(thread),
        'breadcrumb': get_breadcrumb_for_object(thread),
        'posts': posts,
        'pagination': pagination,
        'tags': tags,
    }, 200

def api_get_subforum_last_thread_post(forum_id, subforum_id, thread_id):
    subforum = Subforums.Subforum(subforum_id, forum_id)
    if not subforum.exists():
        return {"status": "error", "reason": "Unknown subforum"}, 404
    return subforum.get_thread_last_post_timestamp(thread_id), 200


if __name__ == '__main__':
    pass

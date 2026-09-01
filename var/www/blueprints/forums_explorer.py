#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: Forum explorer endpoints.
"""

import os
import sys
import json
import shlex

from flask import render_template, jsonify, request, Blueprint, Response, abort, redirect, url_for, send_file
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_read_only, login_admin, login_user_no_api

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import forums_viewer
from lib.ConfigLoader import ConfigLoader
from lib.objects import Forums
from lib import crawlers
from lib import Language
from lib import ail_users
from lib import images_engine
from packages import Date

config_loader = ConfigLoader()
ail_base_url = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None

# ============ BLUEPRINT ============
forums_explorer = Blueprint('forums_explorer', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/forums_explorer'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code


def _get_forum_crawl_management():
    forum_id = request.args.get('id')
    meta = forums_viewer.get_forum_crawl_management(forum_id)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    management = meta[0]
    forum = Forums.Forum(forum_id)
    config = management.get('config', {})
    ail_url = ail_base_url.rstrip('/')
    for account in management.get('accounts', []):
        last_used_at = account.get('last_used_at')
        last_crawled_at = account.get('last_crawled_at')
        account['last_used_at_display'] = Date.get_utc_datetime_from_timestamp(last_used_at) if last_used_at else None
        account['last_crawled_at_display'] = Date.get_utc_datetime_from_timestamp(last_crawled_at) if last_crawled_at else None
        account['has_inflight_crawl'] = bool(account.get('current_crawl_key') and forum.get_inflight_crawl_item(account['current_crawl_key']))
        login_url = forum.get_url() or account.get('current_url')
        login_url = forums_viewer.apply_forum_current_domain(
            login_url, config.get('current_domain')
        )
        account['local_login_url'] = login_url
        if login_url:
            command = [
                './tools/forum_account_local_login.py',
                '--url', login_url,
                '--forum-id', forum_id,
                '--account-id', account['id'],
            ]
            referer = config.get('default_referer') or account.get('current_referer')
            if referer:
                command.extend(['--referer', referer])
            command.extend([
                '--ail-url', ail_url,
                '--api-key', 'YOUR_AIL_API_KEY',
            ])
            account['local_login_command'] = ' '.join(shlex.quote(value) for value in command)
    return management

# ============= ROUTES ==============

@forums_explorer.route("/forums/explorer", methods=['GET'])
@login_required
@login_read_only
def forum_explorer_forums():
    forum_id = request.args.get('id')
    if forum_id:
        meta = forums_viewer.api_get_forum(forum_id)
        if meta[1] != 200:
            return create_json_response(meta[0], meta[1])
        # TODO CREATE OTHER TEMPLATE with NEW ENDPOINT
        return render_template('forums_explorer_forum.html', meta=meta[0], bootstrap_label=bootstrap_label, is_admin=current_user.is_admin())

    forums = forums_viewer.get_forums()
    return render_template('forums_explorer_index.html', forums=forums, bootstrap_label=bootstrap_label, is_admin=current_user.is_admin())


@forums_explorer.route("/forums/explorer/create", methods=['POST'])
@login_required
@login_admin
def forum_explorer_forum_create():
    res = forums_viewer.create_forum(request.form)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('forums_explorer.forum_explorer_crawler_edit', id=res[0]['id']))



@forums_explorer.route("/forums/explorer/banner/edit", methods=['POST'])
@login_required
@login_admin
def forum_explorer_banner_edit():
    forum_id = request.form.get('forum_id')
    action = request.form.get('action')
    if action == 'delete':
        res = forums_viewer.delete_forum_banner(forum_id)
    else:
        res = forums_viewer.update_forum_banner(forum_id, request.files.get('banner'))
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('forums_explorer.forum_explorer_crawler_edit', id=forum_id))


@forums_explorer.route("/forums/explorer/crawler", methods=['GET'])
@login_required
@login_admin
def forum_explorer_crawler_status():
    forum_id = request.args.get('id')
    if forum_id:
        meta = forums_viewer.api_get_forum_crawl_status(forum_id)
        if meta[1] != 200:
            return create_json_response(meta[0], meta[1])
        return render_template('forums_explorer_crawler_forum.html', meta=meta[0], bootstrap_label=bootstrap_label)

    forums = forums_viewer.get_forums_crawl_status()
    return render_template('forums_explorer_crawler_index.html', forums=forums, bootstrap_label=bootstrap_label)


@forums_explorer.route("/forums/explorer/crawler/logs", methods=['GET'])
@login_required
@login_admin
def forum_explorer_crawler_logs():
    try:
        lines = min(max(int(request.args.get('lines') or 100), 10), 1000)
    except (TypeError, ValueError):
        lines = 100
    logs = crawlers.get_last_forum_crawler_logs(lines=lines)
    return render_template(
        'forums_explorer_crawler_logs.html',
        logs=logs,
        lines=lines,
        bootstrap_label=bootstrap_label,
    )


@forums_explorer.route("/forums/explorer/crawler/queue", methods=['GET', 'POST'])
@login_required
@login_admin
def forum_explorer_crawler_queue():
    if request.method == 'POST':
        forum_id = request.form.get('forum_id')
        crawl_key = request.form.get('crawl_key')
        sample_size = request.form.get('sample_size') or 50
        res = forums_viewer.remove_forum_pending_crawl_item(forum_id, crawl_key)
        if res[1] != 200:
            error = res[0].get('reason')
            return redirect(url_for('forums_explorer.forum_explorer_crawler_queue', id=forum_id, sample_size=sample_size, error=error))
        success = f"Removed pending crawl item: {crawl_key}"
        return redirect(url_for('forums_explorer.forum_explorer_crawler_queue', id=forum_id, sample_size=sample_size, success=success))

    forum_id = request.args.get('id')
    sample_size = request.args.get('sample_size') or 50
    meta = forums_viewer.api_get_forum_crawl_queue(forum_id, sample_size=sample_size)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    return render_template('forums_explorer_crawler_queue.html', meta=meta[0], bootstrap_label=bootstrap_label, success=request.args.get('success'), error=request.args.get('error'))



@forums_explorer.route("/forums/explorer/crawler/queue/enqueue", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_queue_enqueue():
    forum_id = request.form.get('forum_id')
    res = forums_viewer.enqueue_forum_root_crawl(forum_id)
    if res[1] != 200:
        error = res[0].get('reason') or res[0].get('error') or 'Unable to enqueue forum crawl'
        return redirect(url_for('forums_explorer.forum_explorer_crawler_queue', id=forum_id, error=error))
    success = f"Queued Forum URL for crawl: {res[0].get('url')}"
    return redirect(url_for('forums_explorer.forum_explorer_crawler_queue', id=forum_id, success=success))

@forums_explorer.route("/forums/explorer/crawler/queue/purge", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_queue_purge():
    forum_id = request.form.get('forum_id')
    res = forums_viewer.purge_forum_crawl_queue(forum_id)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
        # return redirect(url_for('forums_explorer.forum_explorer_crawler_queue', id=forum_id, error=res[0]))
    deleted = res[0].get('deleted', {}) or {}
    success = f"Purged Forum crawl queue: pending={deleted.get('pending_count', 0)}, inflight={deleted.get('inflight_count', 0)}, active={deleted.get('active_dedup_count', 0)}"
    return redirect(url_for('forums_explorer.forum_explorer_crawler_queue', id=forum_id, success=success))


@forums_explorer.route("/forums/explorer/crawler/manage", methods=['GET'])
@login_required
@login_admin
def forum_explorer_crawler_manage():
    meta = _get_forum_crawl_management()
    if isinstance(meta, tuple):
        return meta
    return render_template('forums_explorer_crawler_manage.html', meta=meta, bootstrap_label=bootstrap_label)


@forums_explorer.route("/forums/explorer/crawler/manage/edit", methods=['GET'])
@login_required
@login_admin
def forum_explorer_crawler_edit():
    meta = _get_forum_crawl_management()
    if isinstance(meta, tuple):
        return meta
    return render_template('forums_explorer_crawler_edit.html', meta=meta, bootstrap_label=bootstrap_label)

@forums_explorer.route("/forums/explorer/crawler/config/edit", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_config_edit():
    forum_id = request.form.get('forum_id')
    res = forums_viewer.update_forum_crawl_config(forum_id, request.form)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('forums_explorer.forum_explorer_crawler_edit', id=forum_id))


@forums_explorer.route("/forums/explorer/crawler/account/save", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_account_save():
    forum_id = request.form.get('forum_id')
    account_id = request.form.get('account_id')
    res = forums_viewer.save_forum_crawl_account(forum_id, account_id, request.form)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('forums_explorer.forum_explorer_crawler_edit', id=forum_id))


@forums_explorer.route("/forums/explorer/crawler/account/cookiejar/interactive", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_account_interactive_cookiejar():
    forum_id = request.form.get('forum_id')
    account_id = request.form.get('account_id')
    forum = Forums.Forum(forum_id)
    if not forum.exists():
        return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=forum_id, error='Unknown forum'))
    if not forum.exists_account(account_id):
        return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=forum_id, error='Unknown account'))
    config = forum.get_crawl_config()
    account = forum.get_crawl_account(account_id)
    url = forum.get_url() or account.get_current_url()
    url = forums_viewer.apply_forum_current_domain(url, config.get('current_domain'))
    if not url:
        return redirect(url_for(
            'forums_explorer.forum_explorer_crawler_manage',
            id=forum_id,
            error='Forum login URL is missing',
        ))
    data = {
        'url': url,
        'description': f'Forum {forum_id} account {account_id} browser state',
        'level': 0,
        'forum_id': forum_id,
        'forum_account_id': account_id,
        'proxy': config.get('proxy') or 'force_tor',
        'javascript': config.get('javascript'),
        'browser': 'firefox',
        'user_agent': crawlers.get_default_user_agent(),
        'general_timeout_in_sec': 300,
        'save_cookiejar': True,
        'cookiejar_only': True,
    }
    user_org = current_user.get_org()
    user_id = current_user.get_user_id()
    res = crawlers.api_start_interactive_capture(data, user_org, user_id)
    if res[1] != 200:
        print(res)
        error = res[0].get('error') or 'Unable to start interactive cookiejar session'
        return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=forum_id, error=error))
    return redirect(url_for('crawler_splash.interactive_capture_show', uuid=res[0]['uuid']))


@forums_explorer.route("/forums/explorer/crawler/account/reactivate", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_account_reactivate():
    forum_id = request.form.get('forum_id')
    account_id = request.form.get('account_id')
    next_page = request.form.get('next') or 'manage'
    res = forums_viewer.api_reactivate_errored_forum_crawl_account(forum_id, account_id)
    target = 'forums_explorer.forum_explorer_crawler_status' if next_page == 'status' else 'forums_explorer.forum_explorer_crawler_manage'
    if res[1] != 200:
        error = res[0].get('error') or 'Unable to send account back to crawler queue'
        return redirect(url_for(target, id=forum_id, error=error))
    success = f"Discarded the failed crawl and reactivated account {account_id}"
    return redirect(url_for(target, id=forum_id, success=success))


@forums_explorer.route("/forums/explorer/crawler/account/error/screenshot", methods=['GET'])
@login_required
@login_admin
def forum_explorer_crawler_account_error_screenshot():
    forum_id = request.args.get('forum_id')
    account_id = request.args.get('account_id')
    forum = Forums.Forum(forum_id)
    if not forum.exists() or not forum.exists_account(account_id):
        abort(404)
    account = forum.get_crawl_account(account_id)
    if not account.get_last_error_screenshot_metadata():
        abort(404)
    path = crawlers.get_forum_error_screenshot_path(forum_id, account_id)
    if not os.path.isfile(path):
        abort(404)
    return send_file(
        path,
        mimetype='image/png',
        download_name=f'{forum_id}_{account_id}_last_error.png',
    )


@forums_explorer.route("/forums/explorer/crawler/account/error/html", methods=['GET'])
@login_required
@login_admin
def forum_explorer_crawler_account_error_html():
    forum_id = request.args.get('forum_id')
    account_id = request.args.get('account_id')
    forum = Forums.Forum(forum_id)
    if not forum.exists() or not forum.exists_account(account_id):
        abort(404)
    account = forum.get_crawl_account(account_id)
    if not account.get_error_html_metadata():
        abort(404)
    path = crawlers.get_forum_error_html_path(forum_id, account_id)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, mimetype='text/plain', as_attachment=True, download_name=f'{forum_id}_{account_id}_error.html.txt')


@forums_explorer.route("/forums/explorer/crawler/account/inflight/purge", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_account_inflight_purge():
    forum_id = request.form.get('forum_id')
    account_id = request.form.get('account_id')
    res = forums_viewer.api_purge_forum_account_current_inflight_crawl(forum_id, account_id)
    if res[1] != 200:
        error = res[0].get('error')
        return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=forum_id, error=error))
    success = f"Purged current inflight crawl for account {account_id}"
    return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=forum_id, success=success))


@forums_explorer.route("/forums/explorer/crawler/account/inflight/resend", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_account_inflight_resend():
    forum_id = request.form.get('forum_id')
    account_id = request.form.get('account_id')
    res = forums_viewer.api_resend_forum_account_current_inflight_crawl(forum_id, account_id)
    if res[1] != 200:
        error = res[0].get('error')
        return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=forum_id, error=error))
    success = f"Queued the current crawl again for account {account_id}"
    return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=forum_id, success=success))

@forums_explorer.route("/forums/explorer/crawler/account/delete", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_account_delete():
    forum_id = request.form.get('forum_id')
    account_id = request.form.get('account_id')
    res = forums_viewer.delete_forum_crawl_account(forum_id, account_id)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=forum_id))



@forums_explorer.route("/objects/post/translate", methods=['POST'])
@login_required
@login_user_no_api
def objects_post_translate():
    post_id = request.form.get('id')
    source = request.form.get('language_target')
    target = request.form.get('target')
    translation = request.form.get('translation')
    if target == "Don't Translate":
        target = None
    resp = forums_viewer.api_manually_translate_post(post_id, source, target, translation)
    if resp[1] != 200:
        return create_json_response(resp[0], resp[1])
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for('forums_explorer.forum_explorer_forums'))


@forums_explorer.route("/objects/post/translate/json", methods=['POST'])
@login_required
@login_user_no_api
def objects_post_translate_json():
    post_id = request.form.get('id')
    target = ail_users.AILUser(current_user.get_user_id()).get_preferred_language()
    post, r_code = forums_viewer.api_get_post(post_id, translation_target=target)
    if r_code != 200:
        return create_json_response(post, r_code)
    return jsonify({
        'id': post_id,
        'translation': post.get('translation')
    })

@forums_explorer.route("/objects/post/detect/language", methods=['GET'])
@login_required
@login_user_no_api
def objects_post_detect_language():
    post_id = request.args.get('id')
    resp = forums_viewer.api_post_detect_language(post_id)
    if resp[1] != 200:
        return create_json_response(resp[0], resp[1])
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for('forums_explorer.forum_explorer_forums'))

@forums_explorer.route("/forums/explorer/subforum", methods=['GET'])
@login_required
@login_read_only
def forum_explorer_subforum():
    subtype = request.args.get('subtype')
    subforum_id = request.args.get('id')
    meta = forums_viewer.api_get_subforum(subtype, subforum_id)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    return render_template('forums_explorer_subforum.html', meta=meta[0], bootstrap_label=bootstrap_label)


@forums_explorer.route("/forums/explorer/thread", methods=['GET'])
@login_required
@login_read_only
def forum_explorer_thread():
    subtype = request.args.get('subtype')
    thread_id = request.args.get('id')
    page = request.args.get('page')
    nb = request.args.get('nb')
    target = request.args.get('target')
    meta = forums_viewer.api_get_forum_thread(subtype, thread_id, page=page, nb=nb, translation_target=target)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    languages = Language.get_all_languages()
    translation_languages = Language.get_translation_languages()
    return render_template('forums_explorer_thread.html', meta=meta[0], bootstrap_label=bootstrap_label,
                           ollama_enabled=images_engine.is_ollama_enabled(),
                           ollama_models=images_engine.get_ollama_models(),
                           all_languages=languages, translation_languages=translation_languages, translation_target=target,
                           is_admin=current_user.is_admin())


@forums_explorer.route("/forums/explorer/thread/crawl", methods=['POST'])
@login_required
@login_admin
def forum_explorer_thread_crawl():
    subtype = request.form.get('subtype')
    thread_id = request.form.get('id')
    result, status_code = forums_viewer.api_enqueue_forum_thread_crawl(subtype, thread_id)
    redirect_args = {'subtype': subtype, 'id': thread_id}
    if status_code == 200:
        redirect_args['success'] = 'Thread queued with high priority'
    else:
        error = result.get('error')
        if error == 'already_queued':
            error = 'Thread is already queued'
        redirect_args['error'] = error
    return redirect(url_for('forums_explorer.forum_explorer_thread', **redirect_args))


@forums_explorer.route("/forums/explorer/thread/url/edit", methods=['POST'])
@login_required
@login_admin
def forum_explorer_thread_url_edit():
    subtype = request.form.get('subtype')
    thread_id = request.form.get('id')
    result, status_code = forums_viewer.api_update_forum_thread_url(
        subtype, thread_id, request.form.get('url')
    )
    redirect_args = {'subtype': subtype, 'id': thread_id}
    if status_code == 200:
        redirect_args['success'] = 'Thread URL updated'
    else:
        redirect_args['error'] = result.get('error')
    return redirect(url_for('forums_explorer.forum_explorer_thread', **redirect_args))

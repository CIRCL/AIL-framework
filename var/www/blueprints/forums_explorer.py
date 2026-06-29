#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint Flask: Forum explorer endpoints.
"""

import os
import sys
import json

from flask import render_template, jsonify, request, Blueprint, Response, abort, redirect, url_for
from flask_login import login_required, current_user

# Import Role_Manager
from Role_Manager import login_read_only, login_admin, login_user_no_api

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import forums_viewer
from lib import Language
from lib import ail_users

# ============ BLUEPRINT ============
forums_explorer = Blueprint('forums_explorer', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/forums_explorer'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============

@forums_explorer.route("/chats/explorer/forums", methods=['GET'])
@login_required
@login_read_only
def forum_explorer_forums():
    forum_id = request.args.get('id')
    if forum_id:
        meta = forums_viewer.api_get_forum(forum_id)
        if meta[1] != 200:
            return create_json_response(meta[0], meta[1])
        # TODO CREATE OTHER TEMPLATE with NEW ENDPOINT
        return render_template('forums_explorer_forum.html', meta=meta[0], bootstrap_label=bootstrap_label)

    forums = forums_viewer.get_forums()
    return render_template('forums_explorer_index.html', forums=forums, bootstrap_label=bootstrap_label, is_admin=current_user.is_in_role('admin'))


@forums_explorer.route("/chats/explorer/forums/create", methods=['POST'])
@login_required
@login_admin
def forum_explorer_forum_create():
    res = forums_viewer.create_forum(request.form)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=res[0]['id']))


@forums_explorer.route("/chats/explorer/forums/crawler", methods=['GET'])
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


@forums_explorer.route("/chats/explorer/forums/crawler/queue", methods=['GET'])
@login_required
@login_admin
def forum_explorer_crawler_queue():
    forum_id = request.args.get('id')
    sample_size = request.args.get('sample_size') or 50
    meta = forums_viewer.api_get_forum_crawl_queue(forum_id, sample_size=sample_size)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    return render_template('forums_explorer_crawler_queue.html', meta=meta[0], bootstrap_label=bootstrap_label, success=request.args.get('success'), error=request.args.get('error'))



@forums_explorer.route("/chats/explorer/forums/crawler/queue/enqueue", methods=['POST'])
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

@forums_explorer.route("/chats/explorer/forums/crawler/queue/purge", methods=['POST'])
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


@forums_explorer.route("/chats/explorer/forums/crawler/manage", methods=['GET'])
@login_required
@login_admin
def forum_explorer_crawler_manage():
    forum_id = request.args.get('id')
    meta = forums_viewer.get_forum_crawl_management(forum_id)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    return render_template('forums_explorer_crawler_manage.html', meta=meta[0], bootstrap_label=bootstrap_label)


@forums_explorer.route("/chats/explorer/forums/crawler/config/edit", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_config_edit():
    forum_id = request.form.get('forum_id')
    res = forums_viewer.update_forum_crawl_config(forum_id, request.form)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=forum_id))


@forums_explorer.route("/chats/explorer/forums/crawler/account/save", methods=['POST'])
@login_required
@login_admin
def forum_explorer_crawler_account_save():
    forum_id = request.form.get('forum_id')
    account_id = request.form.get('account_id')
    res = forums_viewer.save_forum_crawl_account(forum_id, account_id, request.form)
    if res[1] != 200:
        return create_json_response(res[0], res[1])
    return redirect(url_for('forums_explorer.forum_explorer_crawler_manage', id=forum_id))



@forums_explorer.route("/chats/explorer/forums/crawler/account/reactivate", methods=['POST'])
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
    success = f"Account {account_id} status updated to waiting and sent back to the forum crawler queue"
    return redirect(url_for(target, id=forum_id, success=success))

@forums_explorer.route("/chats/explorer/forums/crawler/account/delete", methods=['POST'])
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

@forums_explorer.route("/chats/explorer/forum/subforum", methods=['GET'])
@login_required
@login_read_only
def forum_explorer_subforum():
    subtype = request.args.get('subtype')
    subforum_id = request.args.get('id')
    meta = forums_viewer.api_get_subforum(subtype, subforum_id)
    if meta[1] != 200:
        return create_json_response(meta[0], meta[1])
    return render_template('forums_explorer_subforum.html', meta=meta[0], bootstrap_label=bootstrap_label)


@forums_explorer.route("/chats/explorer/forums/thread", methods=['GET'])
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
                           all_languages=languages, translation_languages=translation_languages, translation_target=target)

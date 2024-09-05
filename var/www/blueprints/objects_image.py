#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Blueprint Flask: crawler splash endpoints: dashboard, onion crawler ...
'''

import os
import sys

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file, send_from_directory
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_read_only, no_cache

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import Images
from packages import Date

# ============ BLUEPRINT ============
objects_image = Blueprint('objects_image', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/image'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']


# ============ FUNCTIONS ============
@objects_image.route('/image/<path:filename>')
@login_required
@login_read_only
@no_cache
def image(filename):
    if not filename:
        abort(404)
    if not 64 <= len(filename) <= 70:
        abort(404)
    filename = filename.replace('/', '')
    image = Images.Image(filename)
    return send_from_directory(Images.IMAGE_FOLDER, image.get_rel_path(), as_attachment=False, mimetype='image')


@objects_image.route("/objects/images", methods=['GET'])
@login_required
@login_read_only
def objects_images():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = Images.Images().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    print(dict_objects)

    return render_template("ImageDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)


@objects_image.route("/objects/images/post", methods=['POST'])
@login_required
@login_read_only
def objects_images_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_image.objects_images', date_from=date_from, date_to=date_to, show_objects=show_objects))


@objects_image.route("/objects/images/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_images_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(Images.Images().api_get_chart_nb_by_daterange(date_from, date_to))

# ============= ROUTES ==============


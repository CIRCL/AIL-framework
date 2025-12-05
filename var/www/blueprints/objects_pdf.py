#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
    Blueprint PDF
"""

# import io
import os
import sys
import json

from flask import render_template, jsonify, request, Blueprint, redirect, url_for, Response, abort, send_file, send_from_directory
from flask_login import login_required

# Import Role_Manager
from Role_Manager import login_admin, login_read_only, no_cache

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import PDFs
from lib import Language
from lib import Tag
from packages import Date

# ============ BLUEPRINT ============
objects_pdf = Blueprint('objects_pdf', __name__, template_folder=os.path.join(os.environ['AIL_FLASK'], 'templates/objects/pdf'))

# ============ VARIABLES ============
bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

# ============ FUNCTIONS ============
def create_json_response(data, status_code):
    return Response(json.dumps(data, indent=2, sort_keys=True), mimetype='application/json'), status_code

# ============= ROUTES ==============
@objects_pdf.route('/pdf/pdfa/<string:pdf_id>')
@login_required
@login_read_only
@no_cache
def pdf_pdfa(pdf_id):
    if not pdf_id:
        abort(404)
    if not 64 <= len(pdf_id):
        abort(404)
    pdf_id = pdf_id.replace('/', '')
    pdf = PDFs.PDF(pdf_id)
    return send_from_directory(PDFs.PDF_FOLDER, pdf.get_rel_path(), as_attachment=False, mimetype='pdf')

@objects_pdf.route('/pdf/translate', methods=['POST'])
@login_required
@login_read_only
@no_cache
def pdf_translate():
    obj_id = request.form.get('id')
    source = request.form.get('source')
    target = request.form.get('target')
    r = PDFs.api_create_translation_task(obj_id, source, target, force=True)
    if r[1] != 200:
        return create_json_response(r[0], r[1])
    else:
        if request.referrer:
            return redirect(request.referrer)
        else:
            return create_json_response({'error': 'No Referrer'}, 400)
    # return redirect(url_for('objects_pdf.pdf_view', id=obj_id, task_uuid=r[0]))
    # return send_file(io.BytesIO(r[0]), as_attachment=True, download_name=f'{obj_id}.pdf')

@objects_pdf.route("/pdf/translated", methods=['GET'])
@login_required
@login_read_only
def pdf_translated():
    filename = request.args.get('filename')
    r = PDFs.api_exists_translation_file(filename)
    if r[1] != 200:
        return create_json_response(r[0], r[1])
    return send_from_directory(PDFs.PDF_TRANSLATED_DIR, r[0], as_attachment=False, mimetype='pdf')

@objects_pdf.route("/pdf/translate/task/delete", methods=['GET'])
@login_required
@login_read_only
def pdf_translate_task_delete():
    task_uuid = request.args.get('uuid')
    r = Language.api_delete_translation_task(task_uuid)
    if r[1] != 200:
        return create_json_response(r[0], r[1])
    if request.referrer:
        return redirect(request.referrer)
    else:
        return create_json_response({'error': 'No Referrer'}, 400)

@objects_pdf.route("/pdf/translated/progress", methods=['GET'])
@login_required
@login_read_only
def pdf_translated_progress():
    obj_id = request.args.get('id')
    r = PDFs.api_get_translations_progress(obj_id)
    return create_json_response(r[0], r[1])

@objects_pdf.route("/pdf/view", methods=['GET'])
@login_required
@login_read_only
def pdf_view():
    obj_id = request.args.get('id')
    r = PDFs.api_get_meta(obj_id, options={'author', 'file-meta', 'file-names', 'markdown_id', 'translated', 'svg_icon'}, flask_context=True)
    if r[1] != 200:
        return create_json_response(r[0], r[1])
    meta = r[0]
    return render_template("ShowPDF.html",
                           ail_tags=Tag.get_modal_add_tags(meta['id'], object_type='item'),
                           translation_languages=Language.get_translation_languages(),
                           meta=meta)


@objects_pdf.route("/objects/pdfs", methods=['GET'])
@login_required
@login_read_only
def objects_pdfs():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_objects = request.args.get('show_objects')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']

    if show_objects:
        dict_objects = PDFs.PDFs().api_get_meta_by_daterange(date_from, date_to)
    else:
        dict_objects = {}

    return render_template("PDFDaterange.html", date_from=date_from, date_to=date_to,
                           dict_objects=dict_objects, show_objects=show_objects)


@objects_pdf.route("/objects/pdfs/post", methods=['POST'])
@login_required
@login_read_only
def objects_pdfs_post():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    show_objects = request.form.get('show_objects')
    return redirect(url_for('objects_pdf.objects_pdfs', date_from=date_from, date_to=date_to, show_objects=show_objects))


@objects_pdf.route("/objects/pdfs/range/json", methods=['GET'])
@login_required
@login_read_only
def objects_pdfs_range_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    date = Date.sanitise_date_range(date_from, date_to)
    date_from = date['date_from']
    date_to = date['date_to']
    return jsonify(PDFs.PDFs().api_get_chart_nb_by_daterange(date_from, date_to))

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
from flask import Flask, render_template, jsonify, request, Blueprint, url_for, redirect

import unicodedata
import string
import subprocess
import os
import sys
import datetime
import uuid
from io import BytesIO
from Date import Date
import json

import Paste

from pytaxonomies import Taxonomies
from pymispgalaxies import Galaxies, Clusters

try:
    from pymisp.mispevent import MISPObject
    flag_misp = True
except:
    flag_misp = False
try:
    from thehive4py.models import Case, CaseTask, CustomFieldHelper, CaseObservable
    flag_hive = True
except:
    flag_hive = False

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_serv_tags = Flask_config.r_serv_tags
r_serv_metadata = Flask_config.r_serv_metadata
r_serv_db = Flask_config.r_serv_db
r_serv_log_submit = Flask_config.r_serv_log_submit

pymisp = Flask_config.pymisp
if pymisp is False:
    flag_misp = False

HiveApi = Flask_config.HiveApi
if HiveApi is False:
    flag_hive = False

PasteSubmit = Blueprint('PasteSubmit', __name__, template_folder='templates')

valid_filename_chars = "-_ %s%s" % (string.ascii_letters, string.digits)

ALLOWED_EXTENSIONS = set(['txt', 'sh', 'pdf', 'zip', 'gz', 'tar.gz'])
UPLOAD_FOLDER = Flask_config.UPLOAD_FOLDER

misp_event_url = Flask_config.misp_event_url
hive_case_url = Flask_config.hive_case_url

# ============ FUNCTIONS ============
def one():
    return 1

def allowed_file(filename):
    if not '.' in filename:
        return True
    else:
        return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    # replace characters
    for r in replace:
        filename = filename.replace(r,'_')

    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()

    # keep only whitelisted chars
    return ''.join(c for c in cleaned_filename if c in whitelist)

def launch_submit(ltags, ltagsgalaxies, paste_content, UUID,  password, isfile = False):

    # save temp value on disk
    r_serv_db.set(UUID + ':ltags', ltags)
    r_serv_db.set(UUID + ':ltagsgalaxies', ltagsgalaxies)
    r_serv_db.set(UUID + ':paste_content', paste_content)
    r_serv_db.set(UUID + ':password', password)
    r_serv_db.set(UUID + ':isfile', isfile)

    r_serv_log_submit.set(UUID + ':end', 0)
    r_serv_log_submit.set(UUID + ':processing', 0)
    r_serv_log_submit.set(UUID + ':nb_total', -1)
    r_serv_log_submit.set(UUID + ':nb_end', 0)
    r_serv_log_submit.set(UUID + ':nb_sucess', 0)
    r_serv_log_submit.set(UUID + ':error', 'error:')
    r_serv_log_submit.sadd(UUID + ':paste_submit_link', '')


    # save UUID on disk
    r_serv_db.sadd('submitted:uuid', UUID)


def addTagsVerification(tags, tagsgalaxies):

    list_tag = tags.split(',')
    list_tag_galaxies = tagsgalaxies.split(',')

    taxonomies = Taxonomies()
    active_taxonomies = r_serv_tags.smembers('active_taxonomies')

    active_galaxies = r_serv_tags.smembers('active_galaxies')

    if list_tag != ['']:
        for tag in list_tag:
            # verify input
            tax = tag.split(':')[0]
            if tax in active_taxonomies:
                if tag in r_serv_tags.smembers('active_tag_' + tax):
                    pass
                else:
                    return False
            else:
                return False

    if list_tag_galaxies != ['']:
        for tag in list_tag_galaxies:
            # verify input
            gal = tag.split(':')[1]
            gal = gal.split('=')[0]

            if gal in active_galaxies:
                if tag in r_serv_tags.smembers('active_tag_galaxies_' + gal):
                    pass
                else:
                    return False
            else:
                return False
    return True

def date_to_str(date):
    return "{0}-{1}-{2}".format(date.year, date.month, date.day)

def misp_create_event(distribution, threat_level_id, analysis, info, l_tags, publish, path):

    paste = Paste.Paste(path)
    source = path.split('/')[-6:]
    source = '/'.join(source)[:-3]
    ail_uuid = r_serv_db.get('ail:uuid')
    pseudofile = BytesIO(paste.get_p_content().encode())

    temp = paste._get_p_duplicate()

    #beautifier
    if not temp:
        temp = ''

    p_duplicate_number = len(temp) if len(temp) >= 0 else 0

    to_ret = ""
    for dup in temp[:10]:
        dup = dup.replace('\'','\"').replace('(','[').replace(')',']')
        dup = json.loads(dup)
        algo = dup[0]
        path = dup[1].split('/')[-6:]
        path = '/'.join(path)[:-3] # -3 removes .gz
        if algo == 'tlsh':
            perc = 100 - int(dup[2])
        else:
            perc = dup[2]
        to_ret += "{}: {} [{}%]\n".format(path, algo, perc)
    p_duplicate = to_ret

    today = datetime.date.today()
    # [0-3]
    if publish == 'True':
        published = True
    else:
        published = False
    org_id = None
    orgc_id = None
    sharing_group_id = None
    date = today
    event = pymisp.new_event(distribution, threat_level_id,
            analysis, info, date,
            published, orgc_id, org_id, sharing_group_id)
    eventUuid = event['Event']['uuid']
    eventid = event['Event']['id']

    r_serv_metadata.set('misp_events:'+path, eventid)

    # add tags
    for tag in l_tags:
        pymisp.tag(eventUuid, tag)

    # create attributes
    obj_name = 'ail-leak'
    leak_obj = MISPObject(obj_name)
    leak_obj.add_attribute('sensor', value=ail_uuid, type="text")
    leak_obj.add_attribute('origin', value=source, type='text')
    leak_obj.add_attribute('last-seen', value=date_to_str(paste.p_date), type='datetime')
    leak_obj.add_attribute('raw-data', value=source, data=pseudofile, type="attachment")

    if p_duplicate_number > 0:
        leak_obj.add_attribute('duplicate', value=p_duplicate, type='text')
        leak_obj.add_attribute('duplicate_number', value=p_duplicate_number, type='counter')

    try:
        templateID = [x['ObjectTemplate']['id'] for x in pymisp.get_object_templates_list() if x['ObjectTemplate']['name'] == obj_name][0]
    except IndexError:
        valid_types = ", ".join([x['ObjectTemplate']['name'] for x in pymisp.get_object_templates_list()])
        print ("Template for type {} not found! Valid types are: {%s}".format(obj_name, valid_types))
    r = pymisp.add_object(eventid, templateID, leak_obj)
    if 'errors' in r:
        print(r)
        return False
    else:
        event_url = misp_event_url + eventid
        return event_url

def hive_create_case(hive_tlp, threat_level, hive_description, hive_case_title, l_tags, path):

    ail_uuid = r_serv_db.get('ail:uuid')
    source = path.split('/')[-6:]
    source = '/'.join(source)[:-3]
    # get paste date
    var = path.split('/')
    last_seen = "{0}-{1}-{2}".format(var[-4], var[-3], var[-2])

    case = Case(title=hive_case_title,
                tlp=hive_tlp,
                severity=threat_level,
                flag=False,
                tags=l_tags,
                description='hive_description')

    # Create the case
    id = None
    response = HiveApi.create_case(case)
    if response.status_code == 201:
        id = response.json()['id']

        observ_sensor = CaseObservable(dataType="other", data=[ail_uuid], message="sensor")
        observ_file = CaseObservable(dataType="file", data=[path], tags=l_tags)
        observ_source = CaseObservable(dataType="other", data=[source], message="source")
        observ_last_seen = CaseObservable(dataType="other", data=[last_seen], message="last-seen")

        res = HiveApi.create_case_observable(id,observ_sensor)
        if res.status_code != 201:
            print('ko: {}/{}'.format(res.status_code, res.text))
        res = HiveApi.create_case_observable(id, observ_source)
        if res.status_code != 201:
            print('ko: {}/{}'.format(res.status_code, res.text))
        res = HiveApi.create_case_observable(id, observ_file)
        if res.status_code != 201:
            print('ko: {}/{}'.format(res.status_code, res.text))
        res = HiveApi.create_case_observable(id, observ_last_seen)
        if res.status_code != 201:
            print('ko: {}/{}'.format(res.status_code, res.text))

        r_serv_metadata.set('hive_cases:'+path, id)

        return hive_case_url.replace('id_here', id)
    else:
        print('ko: {}/{}'.format(response.status_code, response.text))
        return False

# ============= ROUTES ==============

@PasteSubmit.route("/PasteSubmit/", methods=['GET'])
def PasteSubmit_page():
    #active taxonomies
    active_taxonomies = r_serv_tags.smembers('active_taxonomies')

    #active galaxies
    active_galaxies = r_serv_tags.smembers('active_galaxies')

    return render_template("PasteSubmit.html",
                            active_taxonomies = active_taxonomies,
                            active_galaxies = active_galaxies)

@PasteSubmit.route("/PasteSubmit/submit", methods=['POST'])
def submit():

    #paste_name = request.form['paste_name']

    password = request.form['password']
    ltags = request.form['tags_taxonomies']
    ltagsgalaxies = request.form['tags_galaxies']
    paste_content = request.form['paste_content']

    is_file = False
    if 'file' in request.files:
        file = request.files['file']
        if file:
            if file.filename:
                is_file = True

    submitted_tag = 'infoleak:submission="manual"'

    #active taxonomies
    active_taxonomies = r_serv_tags.smembers('active_taxonomies')
    #active galaxies
    active_galaxies = r_serv_tags.smembers('active_galaxies')

    if ltags or ltagsgalaxies:
        if not addTagsVerification(ltags, ltagsgalaxies):
            content = 'INVALID TAGS'
            print(content)
            return content, 400

    # add submitted tags
    if(ltags != ''):
        ltags = ltags + ',' + submitted_tag
    else:
        ltags = submitted_tag

    if is_file:
        if file:

            if file and allowed_file(file.filename):

                # get UUID
                UUID = str(uuid.uuid4())

                '''if paste_name:
                    # clean file name
                    UUID = clean_filename(paste_name)'''

                # create submitted dir
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)

                if not '.' in file.filename:
                    full_path = os.path.join(UPLOAD_FOLDER, UUID)
                else:
                    if file.filename[-6:] == 'tar.gz':
                        file_type = 'tar.gz'
                    else:
                        file_type = file.filename.rsplit('.', 1)[1]
                    name = UUID + '.' + file_type
                    full_path = os.path.join(UPLOAD_FOLDER, name)

                #Flask verify the file size
                file.save(full_path)

                paste_content = full_path

                launch_submit(ltags, ltagsgalaxies, paste_content, UUID, password ,True)

                return render_template("submiting.html",
                                            active_taxonomies = active_taxonomies,
                                            active_galaxies = active_galaxies,
                                            UUID = UUID)

            else:
                content = 'wrong file type, allowed_extensions: sh, pdf, zip, gz, tar.gz or remove the extension'
                print(content)
                return content, 400


    elif paste_content != '':
        if sys.getsizeof(paste_content) < 900000:

            # get id
            UUID = str(uuid.uuid4())

            #if paste_name:
                # clean file name
                #id = clean_filename(paste_name)

            launch_submit(ltags, ltagsgalaxies, paste_content, UUID, password)

            return render_template("submiting.html",
                                        active_taxonomies = active_taxonomies,
                                        active_galaxies = active_galaxies,
                                        UUID = UUID)

        else:
            content = 'size error'
            print(content)
            return content, 400

        content = 'submit aborded'
        print(content)
        return content, 400


    return PasteSubmit_page()

@PasteSubmit.route("/PasteSubmit/submit_status", methods=['GET'])
def submit_status():
    UUID = request.args.get('UUID')

    if UUID:
        end = r_serv_log_submit.get(UUID + ':end')
        nb_total = r_serv_log_submit.get(UUID + ':nb_total')
        nb_end = r_serv_log_submit.get(UUID + ':nb_end')
        error = r_serv_log_submit.get(UUID + ':error')
        processing = r_serv_log_submit.get(UUID + ':processing')
        nb_sucess = r_serv_log_submit.get(UUID + ':nb_sucess')
        paste_submit_link = list(r_serv_log_submit.smembers(UUID + ':paste_submit_link'))

        if (end != None) and (nb_total != None) and (nb_end != None) and (error != None) and (processing != None) and (paste_submit_link != None):

            link = ''
            if paste_submit_link:
                for paste in paste_submit_link:
                    url = url_for('showsavedpastes.showsavedpaste') + '?paste=' + paste
                    link += '<a target="_blank" href="' + url + '" class="list-group-item">' + paste +'</a>'

            if nb_total == '-1':
                in_progress = nb_sucess + ' / '
            else:
                in_progress = nb_sucess + ' / ' + nb_total

            if int(nb_total) != 0:
                prog = int(int(nb_end) * 100 / int(nb_total))
            else:
                prog = 0

            if error == 'error:':
                isError = False
            else:
                isError = True

            if end == '0':
                end = False
            else:
                end = True

            if processing == '0':
                processing = False
            else:
                processing = True

            return jsonify(end=end,
                            in_progress=in_progress,
                            prog=prog,
                            link=link,
                            processing=processing,
                            isError=isError,
                            error=error)
        else:
            # FIXME TODO
            print(end)
            print(nb_total)
            print(nb_end)
            print(error)
            print(processing)
            print(nb_sucess)
            return 'to do'
    else:
        return 'INVALID UUID'


@PasteSubmit.route("/PasteSubmit/create_misp_event", methods=['POST'])
def create_misp_event():

    distribution = int(request.form['misp_data[Event][distribution]'])
    threat_level_id = int(request.form['misp_data[Event][threat_level_id]'])
    analysis = int(request.form['misp_data[Event][analysis]'])
    info = request.form['misp_data[Event][info]']
    path = request.form['paste']
    publish = request.form.get('misp_publish')

    #verify input
    if (0 <= distribution <= 3) and (1 <= threat_level_id <= 4) and (0 <= analysis <= 2):

        l_tags = list(r_serv_metadata.smembers('tag:'+path))
        event = misp_create_event(distribution, threat_level_id, analysis, info, l_tags, publish, path)

        if event != False:
            return redirect(event)
        else:
            return 'error, event creation'
    return 'error0'

@PasteSubmit.route("/PasteSubmit/create_hive_case", methods=['POST'])
def create_hive_case():

    hive_tlp = int(request.form['hive_tlp'])
    threat_level = int(request.form['threat_level_hive'])
    hive_description = request.form['hive_description']
    hive_case_title = request.form['hive_case_title']
    path = request.form['paste']

    #verify input
    if (0 <= hive_tlp <= 3) and (1 <= threat_level <= 4):

        l_tags = list(r_serv_metadata.smembers('tag:'+path))
        case = hive_create_case(hive_tlp, threat_level, hive_description, hive_case_title, l_tags, path)

        if case != False:
            return redirect(case)
        else:
            return 'error'

    return 'error'

@PasteSubmit.route("/PasteSubmit/edit_tag_export")
def edit_tag_export():
    misp_auto_events = r_serv_db.get('misp:auto-events')
    hive_auto_alerts = r_serv_db.get('hive:auto-alerts')

    whitelist_misp = r_serv_db.scard('whitelist_misp')
    whitelist_hive = r_serv_db.scard('whitelist_hive')

    list_export_tags = list(r_serv_db.smembers('list_export_tags'))
    status_misp = []
    status_hive = []

    infoleak_tags = Taxonomies().get('infoleak').machinetags()
    is_infoleak_tag = []

    for tag in list_export_tags:
        if r_serv_db.sismember('whitelist_misp', tag):
            status_misp.append(True)
        else:
            status_misp.append(False)

    for tag in list_export_tags:
        if r_serv_db.sismember('whitelist_hive', tag):
            status_hive.append(True)
        else:
            status_hive.append(False)

        if tag in infoleak_tags:
            is_infoleak_tag.append(True)
        else:
            is_infoleak_tag.append(False)

    if misp_auto_events is not None:
        if int(misp_auto_events) == 1:
            misp_active = True
        else:
            misp_active = False
    else:
        misp_active = False

    if hive_auto_alerts is not None:
        if int(hive_auto_alerts)  == 1:
            hive_active = True
        else:
            hive_active = False
    else:
        hive_active = False

    nb_tags = str(r_serv_db.scard('list_export_tags'))
    nb_tags_whitelist_misp = str(r_serv_db.scard('whitelist_misp')) + ' / ' + nb_tags
    nb_tags_whitelist_hive = str(r_serv_db.scard('whitelist_hive')) + ' / ' + nb_tags

    return render_template("edit_tag_export.html",
                            misp_active=misp_active,
                            hive_active=hive_active,
                            list_export_tags=list_export_tags,
                            is_infoleak_tag=is_infoleak_tag,
                            status_misp=status_misp,
                            status_hive=status_hive,
                            nb_tags_whitelist_misp=nb_tags_whitelist_misp,
                            nb_tags_whitelist_hive=nb_tags_whitelist_hive,
                            flag_misp=flag_misp,
                            flag_hive=flag_hive)

@PasteSubmit.route("/PasteSubmit/tag_export_edited", methods=['POST'])
def tag_export_edited():
    tag_enabled_misp = request.form.getlist('tag_enabled_misp')
    tag_enabled_hive = request.form.getlist('tag_enabled_hive')

    list_export_tags = list(r_serv_db.smembers('list_export_tags'))

    r_serv_db.delete('whitelist_misp')
    r_serv_db.delete('whitelist_hive')

    for tag in tag_enabled_misp:
        if r_serv_db.sismember('list_export_tags', tag):
            r_serv_db.sadd('whitelist_misp', tag)
        else:
            return 'invalid input'

    for tag in tag_enabled_hive:
        if r_serv_db.sismember('list_export_tags', tag):
            r_serv_db.sadd('whitelist_hive', tag)
        else:
            return 'invalid input'

    return redirect(url_for('PasteSubmit.edit_tag_export'))

@PasteSubmit.route("/PasteSubmit/enable_misp_auto_event")
def enable_misp_auto_event():
    r_serv_db.set('misp:auto-events', 1)
    return edit_tag_export()

@PasteSubmit.route("/PasteSubmit/disable_misp_auto_event")
def disable_misp_auto_event():
    r_serv_db.set('misp:auto-events', 0)
    return edit_tag_export()

@PasteSubmit.route("/PasteSubmit/enable_hive_auto_alert")
def enable_hive_auto_alert():
    r_serv_db.set('hive:auto-alerts', 1)
    return edit_tag_export()

@PasteSubmit.route("/PasteSubmit/disable_hive_auto_alert")
def disable_hive_auto_alert():
    r_serv_db.set('hive:auto-alerts', 0)
    return edit_tag_export()

@PasteSubmit.route("/PasteSubmit/add_push_tag")
def add_push_tag():
    tag = request.args.get('tag')
    if tag is not None:

        #limit tag length
        if len(tag) > 49:
            tag = tag[0:48]

        r_serv_db.sadd('list_export_tags', tag)

        to_return = {}
        to_return["tag"] = tag
        return jsonify(to_return)
    else:
        return 'None args', 400

@PasteSubmit.route("/PasteSubmit/delete_push_tag")
def delete_push_tag():
    tag = request.args.get('tag')

    infoleak_tags = Taxonomies().get('infoleak').machinetags()
    if tag not in infoleak_tags and r_serv_db.sismember('list_export_tags', tag):
        r_serv_db.srem('list_export_tags', tag)
        r_serv_db.srem('whitelist_misp', tag)
        r_serv_db.srem('whitelist_hive', tag)
        to_return = {}
        to_return["tag"] = tag
        return jsonify(to_return)
    else:
        return 'this tag can\'t be removed', 400

# ========= REGISTRATION =========
app.register_blueprint(PasteSubmit, url_prefix=baseUrl)

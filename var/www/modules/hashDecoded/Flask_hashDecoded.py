#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import os
import sys
import datetime

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, send_file
from Role_Manager import login_admin, login_analyst, login_read_only
from flask_login import login_required

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects import ail_objects

from packages.Date import Date

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
baseUrl = Flask_config.baseUrl
r_serv_metadata = Flask_config.r_serv_metadata
vt_enabled = Flask_config.vt_enabled
vt_auth = Flask_config.vt_auth
PASTES_FOLDER = Flask_config.PASTES_FOLDER

hashDecoded = Blueprint('hashDecoded', __name__, template_folder='templates')

## TODO: put me in option
all_cryptocurrency = ['bitcoin', 'ethereum', 'bitcoin-cash', 'litecoin', 'monero', 'zcash', 'dash']
all_pgpdump = ['key', 'name', 'mail']
all_username = ['telegram', 'twitter', 'jabber']

# ============ FUNCTIONS ============

def get_date_range(num_day):
    curr_date = datetime.date.today()
    date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
    date_list = []

    for i in range(0, num_day+1):
        date_list.append(date.substract_day(i))

    return list(reversed(date_list))

def substract_date(date_from, date_to):
    date_from = datetime.date(int(date_from[0:4]), int(date_from[4:6]), int(date_from[6:8]))
    date_to = datetime.date(int(date_to[0:4]), int(date_to[4:6]), int(date_to[6:8]))
    delta = date_to - date_from # timedelta
    l_date = []
    for i in range(delta.days + 1):
        date = date_from + datetime.timedelta(i)
        l_date.append( date.strftime('%Y%m%d') )
    return l_date


def get_icon(correlation_type, type_id):
    icon_text =  'fas fa-sticky-note'
    if correlation_type == 'pgpdump':
        # set type_id icon
        if type_id == 'key':
            icon_text = 'fas fa-key'
        elif type_id == 'name':
            icon_text = 'fas fa-user-tag'
        elif type_id == 'mail':
            icon_text = 'fas fa-at'
        else:
            icon_text = 'times'
    elif correlation_type == 'cryptocurrency':
        if type_id == 'bitcoin':
            icon_text = 'fab fa-btc'
        elif type_id == 'monero':
            icon_text = 'fab fa-monero'
        elif type_id == 'ethereum':
            icon_text = 'fab fa-ethereum'
        else:
            icon_text = 'fas fa-coins'
    elif correlation_type == 'username':
        if type_id == 'telegram':
            icon_text = 'fab fa-telegram-plane'
        elif type_id == 'twitter':
            icon_text = 'fab fa-twitter'
        elif type_id == 'jabber':
            icon_text = 'fas fa-user'
    return icon_text

def get_icon_text(correlation_type, type_id):
    icon_text = '\uf249'
    if correlation_type == 'pgpdump':
        if type_id == 'key':
            icon_text = '\uf084'
        elif type_id == 'name':
            icon_text = '\uf507'
        elif type_id == 'mail':
            icon_text = '\uf1fa'
        else:
            icon_text = 'times'
    elif correlation_type == 'cryptocurrency':
        if type_id == 'bitcoin':
            icon_text = '\uf15a'
        elif type_id == 'monero':
            icon_text = '\uf3d0'
        elif type_id == 'ethereum':
            icon_text = '\uf42e'
        else:
            icon_text = '\uf51e'
    elif correlation_type == 'username':
        if type_id == 'telegram':
            icon_text = '\uf2c6'
        elif type_id == 'twitter':
            icon_text = '\uf099'
        elif type_id == 'jabber':
            icon_text = '\uf007'
    return icon_text

def get_all_types_id(correlation_type):
    if correlation_type  == 'pgpdump':
        return all_pgpdump
    elif correlation_type == 'cryptocurrency':
        return all_cryptocurrency
    elif correlation_type == 'username':
        return all_username
    else:
        return []

def get_key_id_metadata(obj_type, subtype, obj_id):
    obj = ail_objects.get_object_meta(obj_type, subtype, obj_id)
    return obj._get_meta()

def list_sparkline_type_id_values(date_range_sparkline, correlation_type, type_id, key_id):
    sparklines_value = []
    for date_day in date_range_sparkline:
        nb_seen_this_day = r_serv_metadata.hget('{}:{}:{}'.format(correlation_type, type_id, date_day), key_id)
        if nb_seen_this_day is None:
            nb_seen_this_day = 0
        sparklines_value.append(int(nb_seen_this_day))
    return sparklines_value

def get_correlation_type_search_endpoint(correlation_type):
    if correlation_type == 'pgpdump':
        endpoint = 'hashDecoded.all_pgpdump_search'
    elif correlation_type == 'cryptocurrency':
        endpoint = 'hashDecoded.all_cryptocurrency_search'
    elif correlation_type == 'username':
        endpoint = 'hashDecoded.all_username_search'
    else:
        endpoint = 'hashDecoded.hashDecoded_page'
    return endpoint

def get_correlation_type_page_endpoint(correlation_type):
    if correlation_type == 'pgpdump':
        endpoint = 'hashDecoded.pgpdump_page'
    elif correlation_type == 'cryptocurrency':
        endpoint = 'hashDecoded.cryptocurrency_page'
    elif correlation_type == 'username':
        endpoint = 'hashDecoded.username_page'
    else:
        endpoint = 'hashDecoded.hashDecoded_page'
    return endpoint

def get_show_key_id_endpoint(correlation_type):
    return 'correlation.show_correlation'

def get_range_type_json_endpoint(correlation_type):
    if correlation_type == 'pgpdump':
        endpoint = 'hashDecoded.pgpdump_range_type_json'
    elif correlation_type == 'cryptocurrency':
        endpoint = 'hashDecoded.cryptocurrency_range_type_json'
    elif correlation_type == 'username':
        endpoint = 'hashDecoded.username_range_type_json'
    else:
        endpoint = 'hashDecoded.hashDecoded_page'
    return endpoint

############ CORE CORRELATION ############

def main_correlation_page(correlation_type, type_id, date_from, date_to, show_decoded_files):

    if type_id == 'All types':
        type_id = None

    # verify type input
    if type_id is not None:
        #retrieve char
        type_id = type_id.replace(' ', '')
        if not ail_objects.is_valid_object_subtype(correlation_type, type_id):
            type_id = None

    date_range = []
    if date_from is not None and date_to is not None:
        #change format
        try:
            if len(date_from) != 8:
                date_from = date_from[0:4] + date_from[5:7] + date_from[8:10]
                date_to = date_to[0:4] + date_to[5:7] + date_to[8:10]
            date_range = substract_date(date_from, date_to)
        except:
            pass

    if not date_range:
        date_range.append(datetime.date.today().strftime("%Y%m%d"))
        date_from = date_range[0][0:4] + '-' + date_range[0][4:6] + '-' + date_range[0][6:8]
        date_to = date_from

    else:
        date_from = date_from[0:4] + '-' + date_from[4:6] + '-' + date_from[6:8]
        date_to = date_to[0:4] + '-' + date_to[4:6] + '-' + date_to[6:8]

    # display day type bar chart
    if len(date_range) == 1 and type is None:
        daily_type_chart = True
        daily_date = date_range[0]
    else:
        daily_type_chart = False
        daily_date = None

    if type_id is None:
        all_type_id = get_all_types_id(correlation_type)
    else:
        all_type_id = type_id

    l_keys_id_dump = set()
    if show_decoded_files:
        for date in date_range:
            if isinstance(all_type_id, str):
                l_dump = r_serv_metadata.hkeys('{}:{}:{}'.format(correlation_type, all_type_id, date))
                if l_dump:
                    for dump in l_dump:
                        l_keys_id_dump.add( (dump, all_type_id) )
            else:
                for typ_id in all_type_id:
                    l_dump = r_serv_metadata.hkeys('{}:{}:{}'.format(correlation_type, typ_id, date))
                    if l_dump:
                        for dump in l_dump:
                            l_keys_id_dump.add( (dump, typ_id) )


    num_day_sparkline = 6
    date_range_sparkline = get_date_range(num_day_sparkline)

    sparkline_id = 0
    keys_id_metadata = {}
    for dump_res in l_keys_id_dump:
        new_key_id, typ_id = dump_res

        keys_id_metadata[new_key_id] = get_key_id_metadata(correlation_type, typ_id, new_key_id)

        if keys_id_metadata[new_key_id]:
            keys_id_metadata[new_key_id]['type_id'] = typ_id
            keys_id_metadata[new_key_id]['type_icon'] = get_icon(correlation_type, typ_id)

            keys_id_metadata[new_key_id]['sparklines_data'] = list_sparkline_type_id_values(date_range_sparkline, correlation_type, typ_id, new_key_id)
            keys_id_metadata[new_key_id]['sparklines_id'] = sparkline_id
            sparkline_id += 1

    l_type = get_all_types_id(correlation_type)

    correlation_type_n = correlation_type
    if correlation_type_n=='pgpdump':
        correlation_type_n = 'pgp'

    return render_template("DaysCorrelation.html", all_metadata=keys_id_metadata,
                                                correlation_type=correlation_type,
                                                correlation_type_n=correlation_type_n,
                                                correlation_type_endpoint=get_correlation_type_page_endpoint(correlation_type),
                                                correlation_type_search_endpoint=get_correlation_type_search_endpoint(correlation_type),
                                                show_key_id_endpoint=get_show_key_id_endpoint(correlation_type),
                                                range_type_json_endpoint=get_range_type_json_endpoint(correlation_type),
                                                l_type=l_type, type_id=type_id,
                                                daily_type_chart=daily_type_chart, daily_date=daily_date,
                                                date_from=date_from, date_to=date_to,
                                                show_decoded_files=show_decoded_files)



def correlation_type_range_type_json(correlation_type, date_from, date_to):
    date_range = []
    if date_from is not None and date_to is not None:
        #change format
        if len(date_from) != 8:
            date_from = date_from[0:4] + date_from[5:7] + date_from[8:10]
            date_to = date_to[0:4] + date_to[5:7] + date_to[8:10]
        date_range = substract_date(date_from, date_to)

    if not date_range:
        date_range.append(datetime.date.today().strftime("%Y%m%d"))

    range_type = []
    all_types_id = get_all_types_id(correlation_type)

    # one day
    if len(date_range) == 1:
        for type_id in all_types_id:
            day_type = {}
            # init 0
            for typ_id in all_types_id:
                day_type[typ_id] = 0
            day_type['date'] = type_id
            num_day_type_id = 0
            all_keys = r_serv_metadata.hvals('{}:{}:{}'.format(correlation_type, type_id, date_range[0]))
            if all_keys:
                for val in all_keys:
                    num_day_type_id += int(val)
            day_type[type_id]= num_day_type_id

            #if day_type[type_id] != 0:
            range_type.append(day_type)

    else:
        # display type_id
        for date in date_range:
            day_type = {}
            day_type['date']= date[0:4] + '-' + date[4:6] + '-' + date[6:8]
            for type_id in all_types_id:
                num_day_type_id = 0
                all_keys = r_serv_metadata.hvals('{}:{}:{}'.format(correlation_type, type_id, date))
                if all_keys:
                    for val in all_keys:
                        num_day_type_id += int(val)
                day_type[type_id]= num_day_type_id
            range_type.append(day_type)

    return jsonify(range_type)

# ============= ROUTES ==============


############################ PGPDump ############################

@hashDecoded.route('/decoded/pgp_by_type_json') ## TODO: REFRACTOR
@login_required
@login_read_only
def pgp_by_type_json():
    type_id = request.args.get('type_id')
    date_from = request.args.get('date_from')

    if date_from is None:
        date_from = datetime.date.today().strftime("%Y%m%d")

    #retrieve + char
    type_id = type_id.replace(' ', '+')
    default = False

    if type_id is None:
        default = True
        all_type = ['key', 'name', 'mail']
    else:
        all_type = [ type_id ]

    num_day_type = 30
    date_range = get_date_range(num_day_type)

    #verify input
    if verify_pgp_type_id(type_id) or default:

        type_value = []

        range_decoder = []
        for date in date_range:
            day_type_id = {}
            day_type_id['date']= date[0:4] + '-' + date[4:6] + '-' + date[6:8]
            for type_pgp in all_type:
                all_vals_key = r_serv_metadata.hvals('pgp:{}:date'.format(type_id, date))
                num_day_type_id = 0
                if all_vals_key is not None:
                    for val_key in all_vals_key:
                        num_day_type_id += int(val_key)
                day_type_id[type_pgp]= num_day_type_id
            range_decoder.append(day_type_id)

        return jsonify(range_decoder)
    else:
        return jsonify()

############################ DateRange ############################
@hashDecoded.route("/correlation/pgpdump", methods=['GET'])
@login_required
@login_read_only
def pgpdump_page():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    type_id = request.args.get('type_id')

    show_decoded_files = request.args.get('show_decoded_files')
    res = main_correlation_page('pgpdump', type_id, date_from, date_to, show_decoded_files)
    return res

@hashDecoded.route("/correlation/cryptocurrency", methods=['GET'])
@login_required
@login_read_only
def cryptocurrency_page():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    type_id = request.args.get('type_id')

    show_decoded_files = request.args.get('show_decoded_files')
    res = main_correlation_page('cryptocurrency', type_id, date_from, date_to, show_decoded_files)
    return res

@hashDecoded.route("/correlation/username", methods=['GET'])
@login_required
@login_read_only
def username_page():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    type_id = request.args.get('type_id')

    show_decoded_files = request.args.get('show_decoded_files')
    res = main_correlation_page('username', type_id, date_from, date_to, show_decoded_files)
    return res

@hashDecoded.route("/correlation/all_pgpdump_search", methods=['POST'])
@login_required
@login_read_only
def all_pgpdump_search():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    type_id = request.form.get('type')
    show_decoded_files = request.form.get('show_decoded_files')
    return redirect(url_for('hashDecoded.pgpdump_page', date_from=date_from, date_to=date_to, type_id=type_id, show_decoded_files=show_decoded_files))

@hashDecoded.route("/correlation/all_cryptocurrency_search", methods=['POST'])
@login_required
@login_read_only
def all_cryptocurrency_search():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    type_id = request.form.get('type')
    show_decoded_files = request.form.get('show_decoded_files')
    return redirect(url_for('hashDecoded.cryptocurrency_page', date_from=date_from, date_to=date_to, type_id=type_id, show_decoded_files=show_decoded_files))

@hashDecoded.route("/correlation/all_username_search", methods=['POST'])
@login_required
@login_read_only
def all_username_search():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    type_id = request.form.get('type')
    show_decoded_files = request.form.get('show_decoded_files')
    return redirect(url_for('hashDecoded.username_page', date_from=date_from, date_to=date_to, type_id=type_id, show_decoded_files=show_decoded_files))






@hashDecoded.route('/correlation/cryptocurrency_range_type_json')
@login_required
@login_read_only
def cryptocurrency_range_type_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    return correlation_type_range_type_json('cryptocurrency', date_from, date_to)

@hashDecoded.route('/correlation/pgpdump_range_type_json')
@login_required
@login_read_only
def pgpdump_range_type_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    return correlation_type_range_type_json('pgpdump', date_from, date_to)

@hashDecoded.route('/correlation/username_range_type_json')
@login_required
@login_read_only
def username_range_type_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    return correlation_type_range_type_json('username', date_from, date_to)

##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################


# # TODO: REFRACTOR
@hashDecoded.route('/correlation/pgpdump_graph_line_json')
@login_required
@login_read_only
def pgpdump_graph_line_json():
    type_id = request.args.get('type_id')
    key_id = request.args.get('key_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    return correlation_graph_line_json('pgpdump', type_id, key_id, date_from, date_to)

def correlation_graph_line_json(correlation_type, type_id, key_id, date_from, date_to):
    # verify input
    if key_id is not None and ail_objects.is_valid_object_subtype(correlation_type, type_id) and ail_objects.exists_obj(correlation_type, type_id, key_id):

        if date_from is None or date_to is None:
            nb_days_seen_in_pastes = 30
        else:
            # # TODO: # FIXME:
            nb_days_seen_in_pastes = 30

        date_range_seen_in_pastes = get_date_range(nb_days_seen_in_pastes)

        json_seen_in_paste = []
        for date in date_range_seen_in_pastes:
            nb_seen_this_day = r_serv_metadata.hget('{}:{}:{}'.format(correlation_type, type_id, date), key_id)
            if nb_seen_this_day is None:
                nb_seen_this_day = 0
            date = date[0:4] + '-' + date[4:6] + '-' + date[6:8]
            json_seen_in_paste.append({'date': date, 'value': int(nb_seen_this_day)})

        return jsonify(json_seen_in_paste)
    else:
        return jsonify()

@hashDecoded.route('/correlation/cryptocurrency_graph_line_json')
@login_required
@login_read_only
def cryptocurrency_graph_line_json():
    type_id = request.args.get('type_id')
    key_id = request.args.get('key_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    return correlation_graph_line_json('cryptocurrency', type_id, key_id, date_from, date_to)

@hashDecoded.route('/correlation/username_graph_line_json')
@login_required
@login_read_only
def username_graph_line_json():
    type_id = request.args.get('type_id')
    key_id = request.args.get('key_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    return correlation_graph_line_json('username', type_id, key_id, date_from, date_to)

# ========= REGISTRATION =========
app.register_blueprint(hashDecoded, url_prefix=baseUrl)

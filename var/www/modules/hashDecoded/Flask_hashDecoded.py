#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import os
import datetime
import json
from Date import Date

from io import BytesIO
import zipfile

import requests
from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, send_file

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_serv_metadata = Flask_config.r_serv_metadata
vt_enabled = Flask_config.vt_enabled
vt_auth = Flask_config.vt_auth

hashDecoded = Blueprint('hashDecoded', __name__, template_folder='templates')

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

def list_sparkline_values(date_range_sparkline, hash):
    sparklines_value = []
    for date_day in date_range_sparkline:
        nb_seen_this_day = r_serv_metadata.zscore('hash_date:'+date_day, hash)
        if nb_seen_this_day is None:
            nb_seen_this_day = 0
        sparklines_value.append(int(nb_seen_this_day))
    return sparklines_value

def get_file_icon(estimated_type):
    file_type = estimated_type.split('/')[0]
    # set file icon
    if file_type == 'application':
        file_icon = 'fa-file '
    elif file_type == 'audio':
        file_icon = 'fa-file-video-o '
    elif file_type == 'image':
        file_icon = 'fa-file-image-o'
    elif file_type == 'text':
        file_icon = 'fa-file-text-o'
    else:
        file_icon =  'fa-file-o'

    return file_icon

def get_file_icon_text(estimated_type):
    file_type = estimated_type.split('/')[0]
    # set file icon
    if file_type == 'application':
        file_icon_text = '\uf15b'
    elif file_type == 'audio':
        file_icon_text = '\uf1c7'
    elif file_type == 'image':
        file_icon_text = '\uf1c5'
    elif file_type == 'text':
        file_icon_text = '\uf15c'
    else:
        file_icon_text = '\uf15b'

    return file_icon_text

def one():
    return 1

# ============= ROUTES ==============
@hashDecoded.route("/hashDecoded/all_hash_search", methods=['POST'])
def all_hash_search():
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    type = request.form.get('type')
    encoding = request.form.get('encoding')
    show_decoded_files = request.form.get('show_decoded_files')
    return redirect(url_for('hashDecoded.hashDecoded_page', date_from=date_from, date_to=date_to, type=type, encoding=encoding, show_decoded_files=show_decoded_files))

@hashDecoded.route("/hashDecoded/", methods=['GET'])
def hashDecoded_page():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    type = request.args.get('type')
    encoding = request.args.get('encoding')
    show_decoded_files = request.args.get('show_decoded_files')

    if type == 'All types':
        type = None

    if encoding == 'All encoding':
        encoding = None

    #date_from = '20180628' or date_from = '2018-06-28'
    #date_to = '20180628' or date_to = '2018-06-28'

    # verify file type input
    if type is not None:
        #retrieve + char
        type = type.replace(' ', '+')
        if type not in r_serv_metadata.smembers('hash_all_type'):
            type = None

    all_encoding = r_serv_metadata.smembers('all_decoder')
    # verify encoding input
    if encoding is not None:
        if encoding not in all_encoding:
            encoding = None

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

    l_64 = set()
    if show_decoded_files:
        show_decoded_files = True
        for date in date_range:
            if encoding is None:
                l_hash = r_serv_metadata.zrange('hash_date:' +date, 0, -1)
            else:
                l_hash = r_serv_metadata.zrange(encoding+'_date:' +date, 0, -1)
            if l_hash:
                for hash in l_hash:
                    l_64.add(hash)

    num_day_sparkline = 6
    date_range_sparkline = get_date_range(num_day_sparkline)

    b64_metadata = []
    l_64 = list(l_64)
    for hash in l_64:
        # select requested base 64 type
        estimated_type = r_serv_metadata.hget('metadata_hash:'+hash, 'estimated_type')
        if type is not None:
            if estimated_type is not None:
                if estimated_type != type:
                    continue

        first_seen = r_serv_metadata.hget('metadata_hash:'+hash, 'first_seen')
        last_seen = r_serv_metadata.hget('metadata_hash:'+hash, 'last_seen')
        nb_seen_in_paste = r_serv_metadata.hget('metadata_hash:'+hash, 'nb_seen_in_all_pastes')
        size = r_serv_metadata.hget('metadata_hash:'+hash, 'size')

        if hash is not None and first_seen is not None and \
                                last_seen is not None and \
                                nb_seen_in_paste is not None and \
                                size is not None:

            file_icon = get_file_icon(estimated_type)

            if r_serv_metadata.hexists('metadata_hash:'+hash, 'vt_link'):
                b64_vt = True
                b64_vt_link = r_serv_metadata.hget('metadata_hash:'+hash, 'vt_link')
                b64_vt_report = r_serv_metadata.hget('metadata_hash:'+hash, 'vt_report')
            else:
                b64_vt = False
                b64_vt_link = ''
                b64_vt_report = r_serv_metadata.hget('metadata_hash:'+hash, 'vt_report')
                # hash never refreshed
                if b64_vt_report is None:
                    b64_vt_report = ''

            sparklines_value = list_sparkline_values(date_range_sparkline, hash)

            b64_metadata.append( (file_icon, estimated_type, hash, nb_seen_in_paste, size, first_seen, last_seen, b64_vt, b64_vt_link, b64_vt_report, sparklines_value) )

    l_type = r_serv_metadata.smembers('hash_all_type')

    return render_template("hashDecoded.html", l_64=b64_metadata, vt_enabled=vt_enabled, l_type=l_type, type=type, daily_type_chart=daily_type_chart, daily_date=daily_date,
                                                encoding=encoding, all_encoding=all_encoding, date_from=date_from, date_to=date_to, show_decoded_files=show_decoded_files)

@hashDecoded.route('/hashDecoded/hash_by_type')
def hash_by_type():
    type = request.args.get('type')
    type = 'text/plain'
    return render_template('hash_type.html',type = type)

@hashDecoded.route('/hashDecoded/hash_hash')
def hash_hash():
    hash = request.args.get('hash')
    return render_template('hash_hash.html')

@hashDecoded.route('/hashDecoded/showHash')
def showHash():
    hash = request.args.get('hash')
    #hash = 'e02055d3efaad5d656345f6a8b1b6be4fe8cb5ea'

    # TODO FIXME show error
    if hash is None:
        return hashDecoded_page()

    estimated_type = r_serv_metadata.hget('metadata_hash:'+hash, 'estimated_type')
    # hash not found
    # TODO FIXME show error
    if estimated_type is None:
        return hashDecoded_page()

    else:
        file_icon = get_file_icon(estimated_type)
        size = r_serv_metadata.hget('metadata_hash:'+hash, 'size')
        first_seen = r_serv_metadata.hget('metadata_hash:'+hash, 'first_seen')
        last_seen = r_serv_metadata.hget('metadata_hash:'+hash, 'last_seen')
        nb_seen_in_all_pastes = r_serv_metadata.hget('metadata_hash:'+hash, 'nb_seen_in_all_pastes')

        # get all encoding for this hash
        list_hash_decoder = []
        list_decoder = r_serv_metadata.smembers('all_decoder')
        for decoder in list_decoder:
            encoding = r_serv_metadata.hget('metadata_hash:'+hash, decoder+'_decoder')
            if encoding is not None:
                list_hash_decoder.append({'encoding': decoder, 'nb_seen': encoding})

        num_day_type = 6
        date_range_sparkline = get_date_range(num_day_type)
        sparkline_values = list_sparkline_values(date_range_sparkline, hash)

        if r_serv_metadata.hexists('metadata_hash:'+hash, 'vt_link'):
            b64_vt = True
            b64_vt_link = r_serv_metadata.hget('metadata_hash:'+hash, 'vt_link')
            b64_vt_report = r_serv_metadata.hget('metadata_hash:'+hash, 'vt_report')
        else:
            b64_vt = False
            b64_vt_link = ''
            b64_vt_report = r_serv_metadata.hget('metadata_hash:'+hash, 'vt_report')
            # hash never refreshed
            if b64_vt_report is None:
                b64_vt_report = ''

        return render_template('showHash.html', hash=hash, vt_enabled=vt_enabled, b64_vt=b64_vt, b64_vt_link=b64_vt_link,
                                b64_vt_report=b64_vt_report,
                                size=size, estimated_type=estimated_type, file_icon=file_icon,
                                first_seen=first_seen, list_hash_decoder=list_hash_decoder,
                                last_seen=last_seen, nb_seen_in_all_pastes=nb_seen_in_all_pastes, sparkline_values=sparkline_values)

@hashDecoded.route('/hashDecoded/downloadHash')
def downloadHash():
    hash = request.args.get('hash')
    # sanitize hash
    hash = hash.split('/')[0]

    # hash exist
    if r_serv_metadata.hget('metadata_hash:'+hash, 'estimated_type') is not None:

        b64_path = r_serv_metadata.hget('metadata_hash:'+hash, 'saved_path')
        b64_full_path = os.path.join(os.environ['AIL_HOME'], b64_path)
        hash_content = ''
        try:
            with open(b64_full_path, 'rb') as f:
                hash_content = f.read()

            # zip buffer
            result = BytesIO()
            temp = BytesIO()
            temp.write(hash_content)

            with zipfile.ZipFile(result, "w") as zf:
                #zf.setpassword(b"infected")
                zf.writestr( hash, temp.getvalue())

            filename = hash + '.zip'
            result.seek(0)

            return send_file(result, attachment_filename=filename, as_attachment=True)
        except Exception as e:
            print(e)
            return 'Server Error'
    else:
        return 'hash: ' + hash + " don't exist"

@hashDecoded.route('/hashDecoded/hash_by_type_json')
def hash_by_type_json():
    type = request.args.get('type')

    #retrieve + char
    type = type.replace(' ', '+')

    num_day_type = 30
    date_range = get_date_range(num_day_type)

    #verify input
    if type in r_serv_metadata.smembers('hash_all_type'):
        type_value = []
        all_decoder = r_serv_metadata.smembers('all_decoder')

        range_decoder = []
        for date in date_range:
            day_decoder = {}
            day_decoder['date']= date[0:4] + '-' + date[4:6] + '-' + date[6:8]
            for decoder in all_decoder:
                num_day_decoder = r_serv_metadata.zscore(decoder+'_type:'+type, date)
                if num_day_decoder is None:
                    num_day_decoder = 0
                day_decoder[decoder]= num_day_decoder
            range_decoder.append(day_decoder)



        return jsonify(range_decoder)
    else:
        return jsonify()

@hashDecoded.route('/hashDecoded/decoder_type_json')
def decoder_type_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    typ = request.args.get('type')

    if typ == 'All types':
        typ = None

    # verify file type input
    if typ is not None:
        #retrieve + char
        typ = typ.replace(' ', '+')
        if typ not in r_serv_metadata.smembers('hash_all_type'):
            typ = None

    all_decoder = r_serv_metadata.smembers('all_decoder')
    # sort DESC decoder for color
    all_decoder = sorted(all_decoder)

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

    nb_decoded = {}
    for decoder in all_decoder:
        nb_decoded[decoder] = 0

    for date in date_range:
        for decoder in all_decoder:
            if typ is None:
                nb_decod = r_serv_metadata.get(decoder+'_decoded:'+date)
            else:
                nb_decod = r_serv_metadata.zscore(decoder+'_type:'+typ, date)

            if nb_decod is not None:
                nb_decoded[decoder] = nb_decoded[decoder] + int(nb_decod)

    to_json = []
    for decoder in all_decoder:
        to_json.append({'name': decoder, 'value': nb_decoded[decoder]})
    return jsonify(to_json)

@hashDecoded.route('/hashDecoded/top5_type_json')
def top5_type_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    typ = request.args.get('type')
    decoder = request.args.get('encoding')

    if decoder == 'All encoding' or decoder is None:
        all_decoder = r_serv_metadata.smembers('all_decoder')
    else:
        if not r_serv_metadata.sismember('all_decoder', decoder):
            return jsonify({'Error': 'This decoder do not exist'})
        else:
            all_decoder = [decoder]

    if typ == 'All types' or typ is None or typ=='None':
        all_type = r_serv_metadata.smembers('hash_all_type')
    else:
        typ = typ.replace(' ', '+')
        if not r_serv_metadata.sismember('hash_all_type', typ):
            return jsonify({'Error': 'This type do not exist'})
        else:
            all_type = [typ]

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

    # TODO replace with ZUNIONSTORE
    nb_types_decoded = {}
    for date in date_range:
        for typ in all_type:
            for decoder in all_decoder:
                nb_decoded = r_serv_metadata.zscore('{}_type:{}'.format(decoder, typ), date)
                if nb_decoded is not None:
                    if typ in nb_types_decoded:
                        nb_types_decoded[typ] = nb_types_decoded[typ] + int(nb_decoded)
                    else:
                        nb_types_decoded[typ] = int(nb_decoded)

    to_json = []
    top5_types = sorted(nb_types_decoded, key=nb_types_decoded.get, reverse=True)[:5]
    for typ in top5_types:
        to_json.append({'name': typ, 'value': nb_types_decoded[typ]})
    return jsonify(to_json)


@hashDecoded.route('/hashDecoded/daily_type_json')
def daily_type_json():
    date = request.args.get('date')

    daily_type = set()
    l_b64 = r_serv_metadata.zrange('hash_date:' +date, 0, -1)
    for hash in l_b64:
        estimated_type = r_serv_metadata.hget('metadata_hash:'+hash, 'estimated_type')
        if estimated_type is not None:
            daily_type.add(estimated_type)

    type_value = []
    for day_type in daily_type:
        num_day_type = r_serv_metadata.zscore('hash_type:'+day_type, date)
        type_value.append({ 'date' : day_type, 'value' : int( num_day_type )})

    return jsonify(type_value)

@hashDecoded.route('/hashDecoded/range_type_json')
def range_type_json():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    date_range = []
    if date_from is not None and date_to is not None:
        #change format
        if len(date_from) != 8:
            date_from = date_from[0:4] + date_from[5:7] + date_from[8:10]
            date_to = date_to[0:4] + date_to[5:7] + date_to[8:10]
        date_range = substract_date(date_from, date_to)

    if not date_range:
        date_range.append(datetime.date.today().strftime("%Y%m%d"))

    all_type = set()
    for date in date_range:
        l_hash = r_serv_metadata.zrange('hash_date:' +date, 0, -1)
        if l_hash:
            for hash in l_hash:
                estimated_type = r_serv_metadata.hget('metadata_hash:'+hash, 'estimated_type')
                all_type.add(estimated_type)

    range_type = []

    list_decoder = r_serv_metadata.smembers('all_decoder')
    for date in date_range:
        if len(date_range) == 1:
            if date==date_from and date==date_to:
                for type in all_type:
                    day_type = {}
                    day_type['date']= type
                    for decoder in list_decoder:
                        num_day_decoder = r_serv_metadata.zscore(decoder+'_type:'+type, date)
                        if num_day_decoder is None:
                            num_day_decoder = 0
                        day_type[decoder]= num_day_decoder
                    range_type.append(day_type)
            else:
                range_type = ''
        else:
            day_type = {}
            day_type['date']= date[0:4] + '-' + date[4:6] + '-' + date[6:8]
            for type in all_type:
                num_day_type = 0
                for decoder in list_decoder:
                    num_day_type_decoder = r_serv_metadata.zscore(decoder+'_type:'+type, date)
                    if num_day_type_decoder is not None:
                        num_day_type += num_day_type_decoder
                day_type[type]= num_day_type
            range_type.append(day_type)

    return jsonify(range_type)

@hashDecoded.route('/hashDecoded/hash_graph_line_json')
def hash_graph_line_json():
    hash = request.args.get('hash')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    #hash = '9c748d28d78a64aef99e7ba866a433eb635c6d7a'

    if date_from is None or date_to is None:
        nb_days_seen_in_pastes = 30
    else:
        # # TODO: # FIXME:
        nb_days_seen_in_pastes = 30

    date_range_seen_in_pastes = get_date_range(nb_days_seen_in_pastes)

    #verify input
    if r_serv_metadata.hget('metadata_hash:'+hash, 'estimated_type') is not None:
        json_seen_in_paste = []
        for date in date_range_seen_in_pastes:
            nb_seen_this_day = r_serv_metadata.zscore('hash_date:'+date, hash)
            if nb_seen_this_day is None:
                nb_seen_this_day = 0
            date = date[0:4] + '-' + date[4:6] + '-' + date[6:8]
            json_seen_in_paste.append({ 'date' : date, 'value' : int( nb_seen_this_day )})

        return jsonify(json_seen_in_paste)
    else:
        return jsonify()


@hashDecoded.route('/hashDecoded/hash_graph_node_json')
def hash_graph_node_json():
    hash = request.args.get('hash')

    estimated_type = r_serv_metadata.hget('metadata_hash:'+hash, 'estimated_type')

    if hash is not None and estimated_type is not None:

        nodes_set_hash = set()
        nodes_set_paste = set()
        links_set = set()

        url = hash
        first_seen = r_serv_metadata.hget('metadata_hash:'+hash, 'first_seen')
        last_seen = r_serv_metadata.hget('metadata_hash:'+hash, 'last_seen')
        nb_seen_in_paste = r_serv_metadata.hget('metadata_hash:'+hash, 'nb_seen_in_all_pastes')
        size = r_serv_metadata.hget('metadata_hash:'+hash, 'size')

        nodes_set_hash.add((hash, 1, first_seen, last_seen, estimated_type, nb_seen_in_paste, size, url))

        #get related paste
        l_pastes = r_serv_metadata.zrange('nb_seen_hash:'+hash, 0, -1)
        for paste in l_pastes:
            url = paste
            #nb_seen_in_this_paste = nb_in_file = int(r_serv_metadata.zscore('nb_seen_hash:'+hash, paste))
            nb_hash_in_paste = r_serv_metadata.scard('hash_paste:'+paste)

            nodes_set_paste.add((paste, 2,nb_hash_in_paste,url))
            links_set.add((hash, paste))

            l_hash = r_serv_metadata.smembers('hash_paste:'+paste)
            for child_hash in l_hash:
                if child_hash != hash:
                    url = child_hash
                    first_seen = r_serv_metadata.hget('metadata_hash:'+child_hash, 'first_seen')
                    last_seen = r_serv_metadata.hget('metadata_hash:'+child_hash, 'last_seen')
                    nb_seen_in_paste = r_serv_metadata.hget('metadata_hash:'+child_hash, 'nb_seen_in_all_pastes')
                    size = r_serv_metadata.hget('metadata_hash:'+child_hash, 'size')
                    estimated_type = r_serv_metadata.hget('metadata_hash:'+child_hash, 'estimated_type')

                    nodes_set_hash.add((child_hash, 3, first_seen, last_seen, estimated_type, nb_seen_in_paste, size, url))
                    links_set.add((child_hash, paste))

                    #l_pastes_child = r_serv_metadata.zrange('nb_seen_hash:'+child_hash, 0, -1)
                    #for child_paste in l_pastes_child:

        nodes = []
        for node in nodes_set_hash:
            nodes.append({"id": node[0], "group": node[1], "first_seen": node[2], "last_seen": node[3], 'estimated_type': node[4], "nb_seen_in_paste": node[5], "size": node[6], 'icon': get_file_icon_text(node[4]),"url": url_for('hashDecoded.showHash', hash=node[7]), 'hash': True})
        for node in nodes_set_paste:
            nodes.append({"id": node[0], "group": node[1], "nb_seen_in_paste": node[2],"url": url_for('showsavedpastes.showsavedpaste', paste=node[3]), 'hash': False})
        links = []
        for link in links_set:
            links.append({"source": link[0], "target": link[1]})
        json = {"nodes": nodes, "links": links}
        return jsonify(json)

    else:
        return jsonify({})

@hashDecoded.route('/hashDecoded/hash_types')
def hash_types():
    date_from = 20180701
    date_to = 20180706
    return render_template('hash_types.html', date_from=date_from, date_to=date_to)

@hashDecoded.route('/hashDecoded/send_file_to_vt_js')
def send_file_to_vt_js():
    hash = request.args.get('hash')

    b64_path = r_serv_metadata.hget('metadata_hash:'+hash, 'saved_path')
    b64_full_path = os.path.join(os.environ['AIL_HOME'], b64_path)
    b64_content = ''
    with open(b64_full_path, 'rb') as f:
        b64_content = f.read()

    files = {'file': (hash, b64_content)}
    response = requests.post('https://www.virustotal.com/vtapi/v2/file/scan', files=files, params= {'apikey': vt_auth})
    json_response = response.json()
    #print(json_response)

    vt_link = json_response['permalink'].split('analysis')[0] + 'analysis/'
    r_serv_metadata.hset('metadata_hash:'+hash, 'vt_link', vt_link)
    vt_report = 'Please Refresh'
    r_serv_metadata.hset('metadata_hash:'+hash, 'vt_report', vt_report)

    return jsonify({'vt_link': vt_link, 'vt_report': vt_report})


@hashDecoded.route('/hashDecoded/update_vt_result')
def update_vt_result():
    hash = request.args.get('hash')

    params = {'apikey': vt_auth, 'resource': hash}
    response = requests.get('https://www.virustotal.com/vtapi/v2/file/report',params=params)
    if response.status_code == 200:
        json_response = response.json()
        response_code = json_response['response_code']
        # report exist
        if response_code == 1:
            total = json_response['total']
            positive = json_response['positives']

            b64_vt_report = 'Detection {}/{}'.format(positive,total)
        # no report found
        elif response_code == 0:
            b64_vt_report = 'No report found'
            pass
        # file in queue
        elif response_code == -2:
            b64_vt_report = 'File in queue'
            pass

        r_serv_metadata.hset('metadata_hash:'+hash, 'vt_report', b64_vt_report)
        return jsonify(hash=hash, report_vt=b64_vt_report)
    elif response.status_code == 403:
        Flask_config.vt_enabled = False
        print('VT is disabled')
        return jsonify()
    else:
        # TODO FIXME make json response
        return jsonify()

# ========= REGISTRATION =========
app.register_blueprint(hashDecoded, url_prefix=baseUrl)

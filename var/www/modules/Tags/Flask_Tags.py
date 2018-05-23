#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for

import json

import Paste

from pytaxonomies import Taxonomies

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_tags = Flask_config.r_serv_tags
r_serv_metadata = Flask_config.r_serv_metadata
max_preview_char = Flask_config.max_preview_char
max_preview_modal = Flask_config.max_preview_modal

Tags = Blueprint('Tags', __name__, template_folder='templates')

# ============ FUNCTIONS ============
def one():
    return 1

# ============= ROUTES ==============

@Tags.route("/Tags/", methods=['GET'])
def Tags_page():
    return render_template("Tags.html")

@Tags.route("/Tags/get_all_tags")
def get_all_tags():

    all_tags = r_serv_tags.smembers('list_tags')

    list_tags = []
    for tag in all_tags:
        list_tags.append( tag )

    return jsonify(list_tags)

@Tags.route("/Tags/get_all_tags_taxonomies")
def get_all_tags_taxonomies():

    taxonomies = Taxonomies()
    list_taxonomies = list(taxonomies.keys())

    active_taxonomie = r_serv_tags.smembers('active_taxonomies')

    list_tags = []
    for taxonomie in active_taxonomie:
        #l_tags = taxonomies.get(taxonomie).machinetags()
        l_tags = r_serv_tags.smembers('active_tag_' + taxonomie)
        for tag in l_tags:
            list_tags.append( tag )

    return jsonify(list_tags)

@Tags.route("/Tags/get_tags_taxonomie")
def get_tags_taxonomie():

    taxonomie = request.args.get('taxonomie')

    taxonomies = Taxonomies()
    list_taxonomies = list(taxonomies.keys())

    active_taxonomie = r_serv_tags.smembers('active_taxonomies')

    #verify input
    if taxonomie in list_taxonomies:
        if taxonomie in active_taxonomie:

            list_tags = []
            #l_tags = taxonomies.get(taxonomie).machinetags()
            l_tags = r_serv_tags.smembers('active_tag_' + taxonomie)
            for tag in l_tags:
                list_tags.append( tag )

            return jsonify(list_tags)

        else:
            return 'this taxinomie is disable'
    else:
        return 'INCORRECT INPUT'


@Tags.route("/Tags/get_tagged_paste")
def get_tagged_paste():

    tags = request.args.get('ltags')

    list_tags = tags.split(',')

    # TODO verify input

    if(type(list_tags) is list):
        # no tag
        if list_tags is False:
            print('empty')
        # 1 tag
        elif len(list_tags) < 2:
            tagged_pastes = r_serv_tags.smembers(list_tags[0])

        # 2 tags or more
        else:
            tagged_pastes = r_serv_tags.sinter(list_tags[0], *list_tags[1:])

    else :
        return 'INCORRECT INPUT'

    #currentSelectYear = int(datetime.now().year)
    currentSelectYear = 2018

    bootstrap_label = []
    bootstrap_label.append('primary')
    bootstrap_label.append('success')
    bootstrap_label.append('danger')
    bootstrap_label.append('warning')
    bootstrap_label.append('info')
    bootstrap_label.append('dark')

    all_content = []
    paste_date = []
    paste_linenum = []
    all_path = []
    allPastes = list(tagged_pastes)
    paste_tags = []

    for path in allPastes[0:50]: ######################moduleName
        all_path.append(path)
        paste = Paste.Paste(path)
        content = paste.get_p_content()
        content_range = max_preview_char if len(content)>max_preview_char else len(content)-1
        all_content.append(content[0:content_range].replace("\"", "\'").replace("\r", " ").replace("\n", " "))
        curr_date = str(paste._get_p_date())
        curr_date = curr_date[0:4]+'/'+curr_date[4:6]+'/'+curr_date[6:]
        paste_date.append(curr_date)
        paste_linenum.append(paste.get_lines_info()[0])
        p_tags = r_serv_metadata.smembers('tag:'+path)
        complete_tags = []
        l_tags = []
        for tag in p_tags:
            complete_tag = tag

            tag = tag.split('=')
            if len(tag) > 1:
                if tag[1] != '':
                    tag = tag[1][1:-1]
                # no value
                else:
                    tag = tag[0][1:-1]
            # use for custom tags
            else:
                tag = tag[0]

            l_tags.append( (tag,complete_tag) )

        paste_tags.append(l_tags)

    if len(allPastes) > 10:
        finished = False
    else:
        finished = True

    return render_template("tagged.html",
            year=currentSelectYear,
            all_path=all_path,
            tags=tags,
            paste_tags=paste_tags,
            bootstrap_label=bootstrap_label,
            content=all_content,
            paste_date=paste_date,
            paste_linenum=paste_linenum,
            char_to_display=max_preview_modal,
            finished=finished)


@Tags.route("/Tags/remove_tag")
def remove_tag():

    #TODO verify input
    path = request.args.get('paste')
    tag = request.args.get('tag')

    #remove tag
    r_serv_metadata.srem('tag:'+path, tag)
    r_serv_tags.srem(tag, path)

    return redirect(url_for('showsavedpastes.showsavedpaste', paste=path))

@Tags.route("/Tags/confirm_tag")
def confirm_tag():

    #TODO verify input
    path = request.args.get('paste')
    tag = request.args.get('tag')

    if(tag[9:28] == 'automatic-detection'):

        #remove automatic tag
        r_serv_metadata.srem('tag:'+path, tag)
        r_serv_tags.srem(tag, path)

        tag = tag.replace('automatic-detection','analyst-detection', 1)
        #add analyst tag
        r_serv_metadata.sadd('tag:'+path, tag)
        r_serv_tags.sadd(tag, path)
        #add new tag in list of all used tags
        r_serv_tags.sadd('list_tags', tag)

        return redirect(url_for('showsavedpastes.showsavedpaste', paste=path))

    return 'incompatible tag'

@Tags.route("/Tags/addTags")
def addTags():

    tags = request.args.get('tags')
    path = request.args.get('path')

    list_tag = tags.split(',')

    taxonomies = Taxonomies()
    active_taxonomies = r_serv_tags.smembers('active_taxonomies')

    if not path:
        return 'INCORRECT INPUT'

    for tag in list_tag:
        # verify input
        tax = tag.split(':')[0]
        if tax in active_taxonomies:
            if tag in r_serv_tags.smembers('active_tag_' + tax):

                #add tag
                r_serv_metadata.sadd('tag:'+path, tag)
                r_serv_tags.sadd(tag, path)
                #add new tag in list of all used tags
                r_serv_tags.sadd('list_tags', tag)

            else:
                return 'INCORRECT INPUT'
        else:
            return 'INCORRECT INPUT'

    return redirect(url_for('showsavedpastes.showsavedpaste', paste=path))

@Tags.route("/Tags/thumbs_up_paste")
def thumbs_up_paste():

    #TODO verify input
    path = request.args.get('paste')

    '''positive_t = 'infoleak:confirmed="true-positive"'
    positive_f = 'infoleak:confirmed="false-positive"'

    negative_t = 'infoleak:confirmed="true-negative"'

    list_tags = r_serv_metadata.smembers('tag:'+path)

    if(list_tags > 0):

        if positive_f in list_tags:
            r_serv_metadata.srem('tag:'+path, positive_f)
            r_serv_metadata.sadd('tag:'+path, positive_t)

            r_serv_tags.srem(positive_f, path)
            r_serv_tags.sadd(positive_t, path)
            #add new tag in list of all used tags
            r_serv_tags.sadd('list_tags', positive_t)

            return redirect(url_for('showsavedpastes.showsavedpaste', paste=path))



        if positive_t in list_tags:
            return redirect(url_for('showsavedpastes.showsavedpaste', paste=path))
    else:
        r_serv_metadata.sadd('tag:'+path, negative_t)
        r_serv_tags.sadd(negative_t, path)
        #add new tag in list of all used tags
        r_serv_tags.sadd('list_tags', negative_t)'''

    return redirect(url_for('showsavedpastes.showsavedpaste', paste=path))

@Tags.route("/Tags/thumbs_down_paste")
def thumbs_down_paste():

    #TODO verify input
    path = request.args.get('paste')

    '''list_tags = r_serv_metadata.smembers('tag:'+path)'''

    return redirect(url_for('showsavedpastes.showsavedpaste', paste=path))


@Tags.route("/Tags/taxonomies")
def taxonomies():

    active_taxonomies = r_serv_tags.smembers('active_taxonomies')

    taxonomies = Taxonomies()
    list_taxonomies = list(taxonomies.keys())

    id = []
    name = []
    description = []
    version = []
    enabled = []
    n_tags = []

    for taxonomie in list_taxonomies:
        id.append(taxonomie)
        name.append(taxonomies.get(taxonomie).name)
        description.append(taxonomies.get(taxonomie).description)
        version.append(taxonomies.get(taxonomie).version)
        if taxonomie in active_taxonomies:
            enabled.append(True)
        else:
            enabled.append(False)

        n = str(r_serv_tags.scard('active_tag_' + taxonomie))
        n_tags.append(n + '/' + str(len(taxonomies.get(taxonomie).machinetags())) )

    return render_template("taxonomies.html",
                            id=id,
                            all_name = name,
                            description = description,
                            version = version,
                            enabled = enabled,
                            n_tags=n_tags)
    #return 'O'

@Tags.route("/Tags/edit_taxonomie")
def edit_taxonomie():

    taxonomies = Taxonomies()
    list_taxonomies = list(taxonomies.keys())

    id = request.args.get('taxonomie')

    #verify input
    if id in list(taxonomies.keys()):
        active_tag = r_serv_tags.smembers('active_tag_' + id)
        list_tag = taxonomies.get(id).machinetags()
        list_tag_desc = taxonomies.get(id).machinetags_expanded()

        active_taxonomies = r_serv_tags.smembers('active_taxonomies')
        if id in active_taxonomies:
            active = True
        else:
            active = False

        name = taxonomies.get(id).name
        description = taxonomies.get(id).description
        version = taxonomies.get(id).version

        status = []
        for tag in list_tag:
            if tag in active_tag:
                status.append(True)
            else:
                status.append(False)

        return render_template("edit_taxonomie.html",
            id=id,
            name=name,
            description = description,
            version = version,
            active=active,
            all_tags = list_tag,
            list_tag_desc=list_tag_desc,
            status = status)

    else:
        return 'INVALID TAXONOMIE'

@Tags.route("/Tags/test")
def test():
    return 'test',

@Tags.route("/Tags/disable_taxonomie")
def disable_taxonomie():

    taxonomies = Taxonomies()
    list_taxonomies = list(taxonomies.keys())

    id = request.args.get('taxonomie')

    if id in list_taxonomies:
        r_serv_tags.srem('active_taxonomies', id)
        for tag in taxonomies.get(id).machinetags():
            r_serv_tags.srem('active_tag_' + id, tag)

        return redirect(url_for('Tags.taxonomies'))

    else:
        return "INCORRECT INPUT"



@Tags.route("/Tags/active_taxonomie")
def active_taxonomie():

    taxonomies = Taxonomies()
    list_taxonomies = list(taxonomies.keys())

    id = request.args.get('taxonomie')

    # verify input
    if id in list_taxonomies:
        r_serv_tags.sadd('active_taxonomies', id)
        for tag in taxonomies.get(id).machinetags():
            r_serv_tags.sadd('active_tag_' + id, tag)

        return redirect(url_for('Tags.taxonomies'))

    else:
        return "INCORRECT INPUT"

@Tags.route("/Tags/edit_taxonomie_tag")
def edit_taxonomie_tag():

    taxonomies = Taxonomies()
    list_taxonomies = list(taxonomies.keys())

    arg1 = request.args.getlist('tag_enabled')
    arg2 = request.args.getlist('tag_disabled')

    id = request.args.get('taxonomie')

    #verify input
    if id in list_taxonomies:
        list_tag = taxonomies.get(id).machinetags()

        #check tags validity
        if ( all(elem in list_tag  for elem in arg1) or (len(arg1) == 0) ) and ( all(elem in list_tag  for elem in arg2) or (len(arg2) == 0) ):

            active_tag = r_serv_tags.smembers('active_tag_' + id)

            diff = list(set(arg1) ^ set(list_tag))

            #remove tags
            for tag in diff:
                r_serv_tags.srem('active_tag_' + id, tag)

            #all tags unchecked
            if len(arg1) == 0 and len(arg2) == 0:
                r_serv_tags.srem('active_taxonomies', id)

            #add new tags
            for tag in arg2:
                r_serv_tags.sadd('active_taxonomies', id)
                r_serv_tags.sadd('active_tag_' + id, tag)

            return redirect(url_for('Tags.taxonomies'))
        else:
            return "INCORRECT INPUT"

    else:
        return "INCORRECT INPUT"



# ========= REGISTRATION =========
app.register_blueprint(Tags)

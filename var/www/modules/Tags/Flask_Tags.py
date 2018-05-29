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
from pymispgalaxies import Galaxies, Clusters

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_tags = Flask_config.r_serv_tags
r_serv_metadata = Flask_config.r_serv_metadata
max_preview_char = Flask_config.max_preview_char
max_preview_modal = Flask_config.max_preview_modal

Tags = Blueprint('Tags', __name__, template_folder='templates')

galaxies = Galaxies()
clusters = Clusters(skip_duplicates=True)

list_all_tags = {}
for name, c in clusters.items(): #galaxy name + tags
    list_all_tags[name] = c

list_galaxies = []
for g in galaxies.values():
    list_galaxies.append(g.to_json())

list_clusters = []
for c in clusters.values():
    list_clusters.append(c.to_json())

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
        t = tag.split(':')[0]
        # add synonym
        str_synonyms = ' - synonyms: '
        if t == 'misp-galaxy':
            synonyms = r_serv_tags.smembers('synonym_tag_' + tag)
            for synonym in synonyms:
                str_synonyms = str_synonyms + synonym + ', '
        # add real tag
        if str_synonyms != ' - synonyms: ':
            list_tags.append({'name':tag + str_synonyms,'id':tag})
        else:
            list_tags.append({'name':tag,'id':tag})

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

@Tags.route("/Tags/get_all_tags_galaxies")
def get_all_tags_galaxy():

    active_galaxies = r_serv_tags.smembers('active_galaxies')

    list_tags = []
    for galaxy in active_galaxies:
        l_tags = r_serv_tags.smembers('active_tag_galaxies_' + galaxy)
        for tag in l_tags:
            str_synonyms = ' - synonyms: '
            synonyms = r_serv_tags.smembers('synonym_tag_' + tag)
            # synonyms to display
            for synonym in synonyms:
                str_synonyms = str_synonyms + synonym + ', '
            # add real tag
            if str_synonyms != ' - synonyms: ':
                list_tags.append({'name':tag + str_synonyms,'id':tag})
            else:
                list_tags.append({'name':tag,'id':tag})

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
            return 'this taxonomie is disable'
    else:
        return 'INCORRECT INPUT'

@Tags.route("/Tags/get_tags_galaxy")
def get_tags_galaxy():

    galaxy = request.args.get('galaxy')

    active_galaxies = r_serv_tags.smembers('active_galaxies')

    #verify input
    if galaxy in active_galaxies:

        list_tags = []
        l_tags = r_serv_tags.smembers('active_tag_galaxies_' + galaxy)
        for tag in l_tags:
            synonyms = r_serv_tags.smembers('synonym_tag_' + tag)
            str_synonyms = ' - synonyms: '
            for synonym in synonyms:
                str_synonyms = str_synonyms + synonym + ', '
            # add real tag
            if str_synonyms != ' - synonyms: ':
                list_tags.append({'name':tag + str_synonyms,'id':tag})
            else:
                list_tags.append({'name':tag,'id':tag})

        return jsonify(list_tags)

    else:
        return 'this galaxy is disable'


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

    if r_serv_tags.scard(tag) == 0:
        r_serv_tags.srem('list_tags', tag)

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
    tagsgalaxies = request.args.get('tagsgalaxies')
    path = request.args.get('path')

    list_tag = tags.split(',')
    list_tag_galaxies = tagsgalaxies.split(',')

    taxonomies = Taxonomies()
    active_taxonomies = r_serv_tags.smembers('active_taxonomies')

    active_galaxies = r_serv_tags.smembers('active_galaxies')

    if not path:
        return 'INCORRECT INPUT0'

    if list_tag != ['']:
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
                    return 'INCORRECT INPUT1'
            else:
                return 'INCORRECT INPUT2'

    if list_tag_galaxies != ['']:
        for tag in list_tag_galaxies:
            # verify input
            gal = tag.split(':')[1]
            gal = gal.split('=')[0]
            print(tag)
            print(gal)
            print(active_galaxies)
            if gal in active_galaxies:
                if tag in r_serv_tags.smembers('active_tag_galaxies_' + gal):

                    print('adding ...')
                    #add tag
                    r_serv_metadata.sadd('tag:'+path, tag)
                    r_serv_tags.sadd(tag, path)
                    #add new tag in list of all used tags
                    r_serv_tags.sadd('list_tags', tag)

                else:
                    return 'INCORRECT INPUT3'
            else:
                return 'INCORRECT INPUT4'

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

@Tags.route("/Tags/galaxies")
def galaxies():

    active_galaxies = r_serv_tags.smembers('active_galaxies')

    total_tags = {}
    for name, tags in clusters.items(): #galaxie name + tags
        total_tags[name] = len(tags)

    name = []
    icon = []
    version = []
    all_type = []
    namespace = []
    description = []
    enabled = []
    n_tags = []

    for galaxie_json in list_galaxies:

        galaxie = json.loads(galaxie_json)

        name.append(galaxie['name'])
        icon.append(galaxie['icon'])
        version.append(galaxie['version'])
        type = galaxie['type']
        if type == 'mitre-pre-attack-relashipship':
            type = 'mitre-pre-attack-relationship'
        all_type.append(type)
        namespace.append(galaxie['namespace'])
        description.append(galaxie['description'])


        if type in active_galaxies:
            enabled.append(True)
        else:
            enabled.append(False)

        n = str(r_serv_tags.scard('active_tag_galaxies_' + type))
        n_tags.append(n + '/' + str(total_tags[type]) )

    return render_template("galaxies.html",
                            name=name,
                            icon = icon,
                            version = version,
                            description = description,
                            namespace = namespace,
                            all_type = all_type,
                            enabled = enabled,
                            n_tags=n_tags)


@Tags.route("/Tags/edit_galaxy")
def edit_galaxy():

    id = request.args.get('galaxy')

    for clusters_json in list_clusters:

        #get clusters
        cluster = json.loads(clusters_json)

        if cluster['type'] == id:

            type = id
            active_tag = r_serv_tags.smembers('active_tag_galaxies_' + type)

            name = cluster['name']
            description = cluster['description']
            version = cluster['version']
            source = cluster['source']

            val = cluster['values']

            tags = []
            for data in val:
                try:
                    meta = data['meta']
                    '''synonyms = meta['synonyms']
                    logo = meta['logo']
                    refs = meta['refs']'''
                except KeyError:
                    meta = []
                tag_name = data['value']
                tag_name = 'misp-galaxy:{}="{}"'.format(type, tag_name)
                try:
                    tag_description = data['description']
                except KeyError:
                    tag_description = ''

                tags.append( (tag_name, tag_description, meta) )

            status = []
            for tag in tags:
                if tag[0] in active_tag:
                    status.append(True)
                else:
                    status.append(False)

            active_galaxies = r_serv_tags.smembers('active_galaxies')
            if id in active_galaxies:
                active = True
            else:
                active = False

            return render_template("edit_galaxy.html",
                id = type,
                name = name,
                description = description,
                version = version,
                active = active,
                tags = tags,
                status = status)


    return 'INVALID GALAXY'


@Tags.route("/Tags/active_galaxy")
def active_galaxy():

    id = request.args.get('galaxy')

    # verify input
    try:
        l_tags = list_all_tags[id]
    except KeyError:
        return "INCORRECT INPUT"

    r_serv_tags.sadd('active_galaxies', id)
    for tag in l_tags:
        r_serv_tags.sadd('active_tag_galaxies_' + id, 'misp-galaxy:{}="{}"'.format(id, tag))

    #save synonyms
    for clusters_json in list_clusters:

        #get clusters
        cluster = json.loads(clusters_json)

        if cluster['type'] == id:

            val = cluster['values']

            tags = []
            for data in val:
                try:
                    meta = data['meta']
                    synonyms = meta['synonyms']
                    tag_name = data['value']
                    tag_name = 'misp-galaxy:{}="{}"'.format(id, tag_name)
                    #save synonyms
                    for synonym in synonyms:
                        r_serv_tags.sadd('synonym_tag_' + tag_name, synonym)

                except KeyError:
                    pass

            break

    return redirect(url_for('Tags.galaxies'))


@Tags.route("/Tags/disable_galaxy")
def disable_galaxy():

    id = request.args.get('galaxy')

    # verify input
    try:
        l_tags = list_all_tags[id]
    except KeyError:
        return "INCORRECT INPUT"

    r_serv_tags.srem('active_galaxies', id)
    for tag in l_tags:
        tag_name = 'misp-galaxy:{}="{}"'.format(id, tag)
        r_serv_tags.srem('active_tag_galaxies_' + id, tag_name)
        r_serv_tags.delete('synonym_tag_' + tag_name)

    return redirect(url_for('Tags.galaxies'))


@Tags.route("/Tags/edit_galaxy_tag")
def edit_galaxy_tag():

    arg1 = request.args.getlist('tag_enabled')
    arg2 = request.args.getlist('tag_disabled')

    id = request.args.get('galaxy')

    #verify input
    try:
        l_tags = list_all_tags[id]
    except KeyError:
        return "INCORRECT INPUT"

    #get full tags
    list_tag = []
    for tag in l_tags:
        list_tag.append('misp-galaxy:{}="{}"'.format(id, tag))


    #check tags validity
    if ( all(elem in list_tag  for elem in arg1) or (len(arg1) == 0) ) and ( all(elem in list_tag  for elem in arg2) or (len(arg2) == 0) ):

        active_tag = r_serv_tags.smembers('active_tag_galaxies_' + id)

        diff = list(set(arg1) ^ set(list_tag))

        #remove tags
        for tag in diff:
            r_serv_tags.srem('active_tag_galaxies_' + id, tag)
            r_serv_tags.delete('synonym_tag_' + tag)

        #all tags unchecked
        if len(arg1) == 0 and len(arg2) == 0:
            r_serv_tags.srem('active_galaxies', id)

        #add new tags
        for tag in arg2:
            r_serv_tags.sadd('active_galaxies', id)
            r_serv_tags.sadd('active_tag_galaxies_' + id, tag)

        #get tags synonyms
        for clusters_json in list_clusters:

            #get clusters
            cluster = json.loads(clusters_json)

            if cluster['type'] == id:

                val = cluster['values']

                tags = []
                for data in val:
                    try:
                        meta = data['meta']
                        synonyms = meta['synonyms']
                        tag_name = data['value']
                        tag_name = 'misp-galaxy:{}="{}"'.format(id, tag_name)
                        if tag_name in arg2:
                            #save synonyms
                            for synonym in synonyms:
                                r_serv_tags.sadd('synonym_tag_' + tag_name, synonym)

                    except KeyError:
                        pass
                break

        return redirect(url_for('Tags.galaxies'))

    else:
        return "INCORRECT INPUT"

@Tags.route("/Tags/test")
def test():

    return render_template("test.html",
        id = '1')

# ========= REGISTRATION =========
app.register_blueprint(Tags)

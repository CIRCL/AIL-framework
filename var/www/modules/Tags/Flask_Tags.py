#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for

import json
import datetime

import Paste

from pytaxonomies import Taxonomies
from pymispgalaxies import Galaxies, Clusters

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_serv_tags = Flask_config.r_serv_tags
r_serv_metadata = Flask_config.r_serv_metadata
r_serv_statistics = Flask_config.r_serv_statistics
max_preview_char = Flask_config.max_preview_char
max_preview_modal = Flask_config.max_preview_modal
bootstrap_label = Flask_config.bootstrap_label
max_tags_result = Flask_config.max_tags_result
PASTES_FOLDER = Flask_config.PASTES_FOLDER

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

# tags numbers in galaxies
total_tags = {}
for name, tags in clusters.items(): #galaxie name + tags
    total_tags[name] = len(tags)

# ============ FUNCTIONS ============
def one():
    return 1

def date_substract_day(date, num_day=1):
    new_date = datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8])) - datetime.timedelta(num_day)
    new_date = str(new_date).replace('-', '')
    return new_date

def date_add_day(date, num_day=1):
    new_date = datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8])) + datetime.timedelta(num_day)
    new_date = str(new_date).replace('-', '')
    return new_date

def get_tags_with_synonyms(tag):
    str_synonyms = ' - synonyms: '
    synonyms = r_serv_tags.smembers('synonym_tag_' + tag)
    # synonyms to display
    for synonym in synonyms:
        str_synonyms = str_synonyms + synonym + ', '
    # add real tag
    if str_synonyms != ' - synonyms: ':
        return {'name':tag + str_synonyms,'id':tag}
    else:
        return {'name':tag,'id':tag}

def get_item_date(item_filename):
    l_directory = item_filename.split('/')
    return '{}{}{}'.format(l_directory[-4], l_directory[-3], l_directory[-2])

def substract_date(date_from, date_to):
    date_from = datetime.date(int(date_from[0:4]), int(date_from[4:6]), int(date_from[6:8]))
    date_to = datetime.date(int(date_to[0:4]), int(date_to[4:6]), int(date_to[6:8]))
    delta = date_to - date_from # timedelta
    l_date = []
    for i in range(delta.days + 1):
        date = date_from + datetime.timedelta(i)
        l_date.append( date.strftime('%Y%m%d') )
    return l_date

def get_all_dates_range(date_from, date_to):
    all_dates = {}
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
    all_dates['date_from'] = date_from
    all_dates['date_to'] = date_to
    all_dates['date_range'] = date_range
    return all_dates

def get_last_seen_from_tags_list(list_tags):
    min_last_seen = 99999999
    for tag in list_tags:
        tag_last_seen = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen')
        if tag_last_seen:
            tag_last_seen = int(tag_last_seen)
            if tag_last_seen < min_last_seen:
                min_last_seen = tag_last_seen
    return str(min_last_seen)

def add_item_tag(tag, item_path):
    item_date = int(get_item_date(item_path))

    #add tag
    r_serv_metadata.sadd('tag:{}'.format(item_path), tag)
    r_serv_tags.sadd('{}:{}'.format(tag, item_date), item_path)

    r_serv_tags.hincrby('daily_tags:{}'.format(item_date), tag, 1)

    tag_first_seen = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen')
    if tag_first_seen is None:
        tag_first_seen = 99999999
    else:
        tag_first_seen = int(tag_first_seen)
    tag_last_seen = r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen')
    if tag_last_seen is None:
        tag_last_seen = 0
    else:
        tag_last_seen = int(tag_last_seen)

    #add new tag in list of all used tags
    r_serv_tags.sadd('list_tags', tag)

    # update fisrt_seen/last_seen
    if item_date < tag_first_seen:
        r_serv_tags.hset('tag_metadata:{}'.format(tag), 'first_seen', item_date)

    # update metadata last_seen
    if item_date > tag_last_seen:
        r_serv_tags.hset('tag_metadata:{}'.format(tag), 'last_seen', item_date)

def remove_item_tag(tag, item_path):
    item_date = int(get_item_date(item_path))

    #remove tag
    r_serv_metadata.srem('tag:{}'.format(item_path), tag)
    res = r_serv_tags.srem('{}:{}'.format(tag, item_date), item_path)

    if res ==1:
        # no tag for this day
        if int(r_serv_tags.hget('daily_tags:{}'.format(item_date), tag)) == 1:
            r_serv_tags.hdel('daily_tags:{}'.format(item_date), tag)
        else:
            r_serv_tags.hincrby('daily_tags:{}'.format(item_date), tag, -1)

        tag_first_seen = int(r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen'))
        tag_last_seen = int(r_serv_tags.hget('tag_metadata:{}'.format(tag), 'last_seen'))
        # update fisrt_seen/last_seen
        if item_date == tag_first_seen:
            update_tag_first_seen(tag, tag_first_seen, tag_last_seen)
        if item_date == tag_last_seen:
            update_tag_last_seen(tag, tag_first_seen, tag_last_seen)
    else:
        return 'Error incorrect tag'

def update_tag_first_seen(tag, tag_first_seen, tag_last_seen):
    if tag_first_seen == tag_last_seen:
        if r_serv_tags.scard('{}:{}'.format(tag, tag_first_seen)) > 0:
            r_serv_tags.hset('tag_metadata:{}'.format(tag), 'first_seen', tag_first_seen)
        # no tag in db
        else:
            r_serv_tags.srem('list_tags', tag)
            r_serv_tags.hdel('tag_metadata:{}'.format(tag), 'first_seen')
            r_serv_tags.hdel('tag_metadata:{}'.format(tag), 'last_seen')
    else:
        if r_serv_tags.scard('{}:{}'.format(tag, tag_first_seen)) > 0:
            r_serv_tags.hset('tag_metadata:{}'.format(tag), 'first_seen', tag_first_seen)
        else:
            tag_first_seen = date_add_day(tag_first_seen)
            update_tag_first_seen(tag, tag_first_seen, tag_last_seen)

def update_tag_last_seen(tag, tag_first_seen, tag_last_seen):
    if tag_first_seen == tag_last_seen:
        if r_serv_tags.scard('{}:{}'.format(tag, tag_last_seen)) > 0:
            r_serv_tags.hset('tag_metadata:{}'.format(tag), 'last_seen', tag_last_seen)
        # no tag in db
        else:
            r_serv_tags.srem('list_tags', tag)
            r_serv_tags.hdel('tag_metadata:{}'.format(tag), 'first_seen')
            r_serv_tags.hdel('tag_metadata:{}'.format(tag), 'last_seen')
    else:
        if r_serv_tags.scard('{}:{}'.format(tag, tag_last_seen)) > 0:
            r_serv_tags.hset('tag_metadata:{}'.format(tag), 'last_seen', tag_last_seen)
        else:
            tag_last_seen = date_substract_day(tag_last_seen)
            update_tag_last_seen(tag, tag_first_seen, tag_last_seen)

# ============= ROUTES ==============

@Tags.route("/tags/", methods=['GET'])
def Tags_page():
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    tags = request.args.get('ltags')

    if tags is None:
        dates = get_all_dates_range(date_from, date_to)
        return render_template("Tags.html", date_from=dates['date_from'], date_to=dates['date_to'])

    # unpack tags
    list_tags = tags.split(',')
    list_tag = []
    for tag in list_tags:
        list_tag.append(tag.replace('"','\"'))

    #no search by date, use last_seen for  date_from/date_to
    if date_from is None and date_to is None and tags is not None:
        date_from = get_last_seen_from_tags_list(list_tags)
        date_to = date_from

    # TODO verify input

    dates = get_all_dates_range(date_from, date_to)

    if(type(list_tags) is list):
        # no tag
        if list_tags is False:
            print('empty')
        # 1 tag
        elif len(list_tags) < 2:
            tagged_pastes = []
            for date in dates['date_range']:
                tagged_pastes.extend(r_serv_tags.smembers('{}:{}'.format(list_tags[0], date)))

        # 2 tags or more
        else:
            tagged_pastes = []
            for date in dates['date_range']:
                tag_keys = []
                for tag in list_tags:
                    tag_keys.append('{}:{}'.format(tag, date))

                if len(tag_keys) > 1:
                    daily_items = r_serv_tags.sinter(tag_keys[0], *tag_keys[1:])
                else:
                    daily_items = r_serv_tags.sinter(tag_keys[0])
                tagged_pastes.extend(daily_items)

    else :
        return 'INCORRECT INPUT'

    all_content = []
    paste_date = []
    paste_linenum = []
    all_path = []
    allPastes = list(tagged_pastes)
    paste_tags = []

    try:
        page = int(request.args.get('page'))
    except:
        page = 1
    if page <= 0:
        page = 1
    nb_page_max = len(tagged_pastes)/(max_tags_result)
    if not nb_page_max.is_integer():
        nb_page_max = int(nb_page_max)+1
    else:
        nb_page_max = int(nb_page_max)
    if page > nb_page_max:
        page = nb_page_max
    start = max_tags_result*(page -1)
    stop = max_tags_result*page

    for path in allPastes[start:stop]:
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

    if len(list_tag) == 1:
        tag_nav=tags.replace('"', '').replace('=', '').replace(':', '')
    else:
        tag_nav='empty'

    return render_template("Tags.html",
            all_path=all_path,
            tags=tags,
            tag_nav=tag_nav,
            list_tag = list_tag,
            date_from=dates['date_from'],
            date_to=dates['date_to'],
            page=page, nb_page_max=nb_page_max,
            paste_tags=paste_tags,
            bootstrap_label=bootstrap_label,
            content=all_content,
            paste_date=paste_date,
            paste_linenum=paste_linenum,
            char_to_display=max_preview_modal,
            finished=finished)


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
            list_tags.append(get_tags_with_synonyms(tag))

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
            list_tags.append(get_tags_with_synonyms(tag))

        return jsonify(list_tags)

    else:
        return 'this galaxy is disable'

@Tags.route("/Tags/remove_tag")
def remove_tag():

    #TODO verify input
    path = request.args.get('paste')
    tag = request.args.get('tag')

    remove_item_tag(tag, path)

    return redirect(url_for('showsavedpastes.showsavedpaste', paste=path))

@Tags.route("/Tags/confirm_tag")
def confirm_tag():

    #TODO verify input
    path = request.args.get('paste')
    tag = request.args.get('tag')

    if(tag[9:28] == 'automatic-detection'):
        remove_item_tag(tag, path)

        tag = tag.replace('automatic-detection','analyst-detection', 1)
        #add analyst tag
        add_item_tag(tag, path)

        return redirect(url_for('showsavedpastes.showsavedpaste', paste=path))

    return 'incompatible tag'

@Tags.route("/Tags/tag_validation")
def tag_validation():

    path = request.args.get('paste')
    tag = request.args.get('tag')
    status = request.args.get('status')

    if (status == 'fp' or status == 'tp') and r_serv_tags.sismember('list_tags', tag):

        if status == 'tp':
            r_serv_statistics.sadd('tp:'+tag, path)
            r_serv_statistics.srem('fp:'+tag, path)
        else:
            r_serv_statistics.sadd('fp:'+tag, path)
            r_serv_statistics.srem('tp:'+tag, path)

        return redirect(url_for('showsavedpastes.showsavedpaste', paste=path))
    else:
        return 'input error'

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
                    add_item_tag(tag, path)

                else:
                    return 'INCORRECT INPUT1'
            else:
                return 'INCORRECT INPUT2'

    if list_tag_galaxies != ['']:
        for tag in list_tag_galaxies:
            # verify input
            gal = tag.split(':')[1]
            gal = gal.split('=')[0]

            if gal in active_galaxies:
                if tag in r_serv_tags.smembers('active_tag_galaxies_' + gal):
                    add_item_tag(tag, path)

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

        n = str(r_serv_tags.scard('active_tag_' + id))
        badge = n + '/' + str(len(taxonomies.get(id).machinetags()))

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
            badge = badge,
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

            n = str(r_serv_tags.scard('active_tag_galaxies_' + type))
            badge = n + '/' + str(total_tags[type])

            name = cluster['name']
            description = cluster['description']
            version = cluster['version']
            source = cluster['source']

            val = cluster['values']

            tags = []
            for data in val:
                try:
                    meta = data['meta']
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
                badge = badge,
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

@Tags.route("/Tags/tag_galaxy_info")
def tag_galaxy_info():

    galaxy = request.args.get('galaxy')
    tag = request.args.get('tag')

    full_tag = tag
    title = tag.split(':')[1]
    tag = tag.split('=')[1]
    tag = tag[1:-1]

    #get clusters
    for clusters_json in list_clusters:
        cluster = json.loads(clusters_json)

        if cluster['type'] == galaxy:
            val = cluster['values']
            source = cluster['source']

            for data in val:
                if tag == data['value']:
                    try:
                        description = data['description']
                    except KeyError:
                        description = ''
                    if r_serv_tags.sismember('active_tag_galaxies_' + galaxy, full_tag):
                        active = True
                    else:
                        active = False

                    synonyms = []
                    metadata = []
                    list_metadata = []
                    try:
                        meta = data['meta']
                        for key in meta:
                            if key != 'synonyms':
                                if type(meta[key]) is list:
                                    for item in meta[key]:
                                        list_metadata.append(key + ' :    ' + item)
                                else:
                                    list_metadata.append(key + ' :    ' + meta[key])
                        try:
                            synonyms = meta['synonyms']
                            bool_synonyms = True
                        except KeyError:
                            synonyms = []
                            bool_synonyms = False
                    except KeyError:
                        pass

                    if synonyms:
                        bool_synonyms = True
                    else:
                        bool_synonyms = False
                    if list_metadata:
                        metadata = True
                    else:
                        metadata = False

                    return render_template("tag_galaxy_info.html",
                                title = title,
                                description = description,
                                source = source,
                                active = active,
                                synonyms = synonyms,
                                bool_synonyms = bool_synonyms,
                                metadata = metadata,
                                list_metadata = list_metadata)

    return 'INVALID INPUT'

# ========= REGISTRATION =========
app.register_blueprint(Tags, url_prefix=baseUrl)

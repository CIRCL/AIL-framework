#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page

    note: The matching of credential against supplied credential is done using Levenshtein distance
'''
import redis
import datetime
import calendar
import flask
from flask import Flask, render_template, jsonify, request, Blueprint, url_for, redirect
import re
import Paste
from pprint import pprint
import Levenshtein

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
baseUrl = Flask_config.baseUrl
r_serv_term = Flask_config.r_serv_term
r_serv_cred = Flask_config.r_serv_cred
r_serv_db = Flask_config.r_serv_db
bootstrap_label = Flask_config.bootstrap_label

terms = Blueprint('terms', __name__, template_folder='templates')

'''TERM'''
DEFAULT_MATCH_PERCENT = 50

#tracked
TrackedTermsSet_Name = "TrackedSetTermSet"
TrackedTermsDate_Name = "TrackedTermDate"
#black
BlackListTermsDate_Name = "BlackListTermDate"
BlackListTermsSet_Name = "BlackListSetTermSet"
#regex
TrackedRegexSet_Name = "TrackedRegexSet"
TrackedRegexDate_Name = "TrackedRegexDate"
#set
TrackedSetSet_Name = "TrackedSetSet"
TrackedSetDate_Name = "TrackedSetDate"

# notifications enabled/disabled
# same value as in `bin/NotificationHelper.py`
TrackedTermsNotificationEnabled_Name = "TrackedNotifications"

# associated notification email addresses for a specific term`
# same value as in `bin/NotificationHelper.py`
# Keys will be e.g. TrackedNotificationEmails_<TERMNAME>
TrackedTermsNotificationEmailsPrefix_Name = "TrackedNotificationEmails_"
TrackedTermsNotificationTagsPrefix_Name = "TrackedNotificationTags_"

'''CRED'''
REGEX_CRED = '[a-z]+|[A-Z]{3,}|[A-Z]{1,2}[a-z]+|[0-9]+'
REDIS_KEY_NUM_USERNAME = 'uniqNumForUsername'
REDIS_KEY_NUM_PATH = 'uniqNumForUsername'
REDIS_KEY_ALL_CRED_SET = 'AllCredentials'
REDIS_KEY_ALL_CRED_SET_REV = 'AllCredentialsRev'
REDIS_KEY_ALL_PATH_SET = 'AllPath'
REDIS_KEY_ALL_PATH_SET_REV = 'AllPathRev'
REDIS_KEY_MAP_CRED_TO_PATH = 'CredToPathMapping'



# ============ FUNCTIONS ============

def Term_getValueOverRange(word, startDate, num_day, per_paste=""):
    passed_days = 0
    oneDay = 60*60*24
    to_return = []
    curr_to_return = 0
    for timestamp in range(startDate, startDate - max(num_day)*oneDay, -oneDay):
        value = r_serv_term.hget(per_paste+str(timestamp), word)
        curr_to_return += int(value) if value is not None else 0
        for i in num_day:
            if passed_days == i-1:
                to_return.append(curr_to_return)
        passed_days += 1
    return to_return

#Mix suplied username, if extensive is set, slice username(s) with different windows
def mixUserName(supplied, extensive=False):
    #e.g.: John Smith
    terms = supplied.split()[:2]
    usernames = []
    if len(terms) == 1:
        terms.append(' ')

    #john, smith, John, Smith, JOHN, SMITH
    usernames += [terms[0].lower()]
    usernames += [terms[1].lower()]
    usernames += [terms[0][0].upper() + terms[0][1:].lower()]
    usernames += [terms[1][0].upper() + terms[1][1:].lower()]
    usernames += [terms[0].upper()]
    usernames += [terms[1].upper()]

    #johnsmith, smithjohn, JOHNsmith, johnSMITH, SMITHjohn, smithJOHN
    usernames += [(terms[0].lower() + terms[1].lower()).strip()]
    usernames += [(terms[1].lower() + terms[0].lower()).strip()]
    usernames += [(terms[0].upper() + terms[1].lower()).strip()]
    usernames += [(terms[0].lower() + terms[1].upper()).strip()]
    usernames += [(terms[1].upper() + terms[0].lower()).strip()]
    usernames += [(terms[1].lower() + terms[0].upper()).strip()]
    #Jsmith, JSmith, jsmith, jSmith, johnS, Js, JohnSmith, Johnsmith, johnSmith
    usernames += [(terms[0][0].upper() + terms[1][0].lower() + terms[1][1:].lower()).strip()]
    usernames += [(terms[0][0].upper() + terms[1][0].upper() + terms[1][1:].lower()).strip()]
    usernames += [(terms[0][0].lower() + terms[1][0].lower() + terms[1][1:].lower()).strip()]
    usernames += [(terms[0][0].lower() + terms[1][0].upper() + terms[1][1:].lower()).strip()]
    usernames += [(terms[0].lower() + terms[1][0].upper()).strip()]
    usernames += [(terms[0].upper() + terms[1][0].lower()).strip()]
    usernames += [(terms[0][0].upper() + terms[0][1:].lower() + terms[1][0].upper() + terms[1][1:].lower()).strip()]
    usernames += [(terms[0][0].upper() + terms[0][1:].lower() + terms[1][0].lower() + terms[1][1:].lower()).strip()]
    usernames += [(terms[0][0].lower() + terms[0][1:].lower() + terms[1][0].upper() + terms[1][1:].lower()).strip()]

    if not extensive:
        return usernames

    #Slice the supplied username(s)
    mixedSupplied = supplied.replace(' ','')
    minWindow = 3 if len(mixedSupplied)/2 < 4 else len(mixedSupplied)/2
    for winSize in range(3,len(mixedSupplied)):
        for startIndex in range(0, len(mixedSupplied)-winSize):
            usernames += [mixedSupplied[startIndex:startIndex+winSize]]

    filtered_usernames = []
    for usr in usernames:
        if len(usr) > 2:
            filtered_usernames.append(usr)
    return filtered_usernames

def save_tag_to_auto_push(list_tag):
    for tag in set(list_tag):
        #limit tag length
        if len(tag) > 49:
            tag = tag[0:48]
        r_serv_db.sadd('list_export_tags', tag)

# ============ ROUTES ============

@terms.route("/terms_management/")
def terms_management():
    per_paste = request.args.get('per_paste')
    if per_paste == "1" or per_paste is None:
        per_paste_text = "per_paste_"
        per_paste = 1
    else:
        per_paste_text = ""
        per_paste = 0

    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())

    # Map tracking if notifications are enabled for a specific term
    notificationEnabledDict = {}

    # Maps a specific term to the associated email addresses
    notificationEMailTermMapping = {}
    notificationTagsTermMapping = {}

    #Regex
    trackReg_list = []
    trackReg_list_values = []
    trackReg_list_num_of_paste = []
    for tracked_regex in r_serv_term.smembers(TrackedRegexSet_Name):

        notificationEMailTermMapping[tracked_regex] = r_serv_term.smembers(TrackedTermsNotificationEmailsPrefix_Name + tracked_regex)
        notificationTagsTermMapping[tracked_regex] = r_serv_term.smembers(TrackedTermsNotificationTagsPrefix_Name + tracked_regex)

        if tracked_regex not in notificationEnabledDict:
            notificationEnabledDict[tracked_regex] = False

        trackReg_list.append(tracked_regex)
        value_range = Term_getValueOverRange(tracked_regex, today_timestamp, [1, 7, 31], per_paste=per_paste_text)

        term_date = r_serv_term.hget(TrackedRegexDate_Name, tracked_regex)

        set_paste_name = "regex_" + tracked_regex
        trackReg_list_num_of_paste.append(r_serv_term.scard(set_paste_name))
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        value_range.append(term_date)
        trackReg_list_values.append(value_range)

        if tracked_regex in r_serv_term.smembers(TrackedTermsNotificationEnabled_Name):
            notificationEnabledDict[tracked_regex] = True

    #Set
    trackSet_list = []
    trackSet_list_values = []
    trackSet_list_num_of_paste = []
    for tracked_set in r_serv_term.smembers(TrackedSetSet_Name):
        tracked_set = tracked_set

        notificationEMailTermMapping[tracked_set] = r_serv_term.smembers(TrackedTermsNotificationEmailsPrefix_Name + tracked_set)
        notificationTagsTermMapping[tracked_set] = r_serv_term.smembers(TrackedTermsNotificationTagsPrefix_Name + tracked_set)

        if tracked_set not in notificationEnabledDict:
            notificationEnabledDict[tracked_set] = False

        trackSet_list.append(tracked_set)
        value_range = Term_getValueOverRange(tracked_set, today_timestamp, [1, 7, 31], per_paste=per_paste_text)

        term_date = r_serv_term.hget(TrackedSetDate_Name, tracked_set)

        set_paste_name = "set_" + tracked_set
        trackSet_list_num_of_paste.append(r_serv_term.scard(set_paste_name))
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        value_range.append(term_date)
        trackSet_list_values.append(value_range)

        if tracked_set in r_serv_term.smembers(TrackedTermsNotificationEnabled_Name):
            notificationEnabledDict[tracked_set] = True

    #Tracked terms
    track_list = []
    track_list_values = []
    track_list_num_of_paste = []
    for tracked_term in r_serv_term.smembers(TrackedTermsSet_Name):

        notificationEMailTermMapping[tracked_term] = r_serv_term.smembers(TrackedTermsNotificationEmailsPrefix_Name + tracked_term)
        notificationTagsTermMapping[tracked_term] = r_serv_term.smembers(TrackedTermsNotificationTagsPrefix_Name + tracked_term)

        if tracked_term not in notificationEnabledDict:
            notificationEnabledDict[tracked_term] = False

        track_list.append(tracked_term)
        value_range = Term_getValueOverRange(tracked_term, today_timestamp, [1, 7, 31], per_paste=per_paste_text)

        term_date = r_serv_term.hget(TrackedTermsDate_Name, tracked_term)

        set_paste_name = "tracked_" + tracked_term

        track_list_num_of_paste.append( r_serv_term.scard(set_paste_name) )

        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        value_range.append(term_date)
        track_list_values.append(value_range)

        if tracked_term in r_serv_term.smembers(TrackedTermsNotificationEnabled_Name):
            notificationEnabledDict[tracked_term] = True

    #blacklist terms
    black_list = []
    for blacked_term in r_serv_term.smembers(BlackListTermsSet_Name):
        term_date = r_serv_term.hget(BlackListTermsDate_Name, blacked_term)
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        black_list.append([blacked_term, term_date])

    return render_template("terms_management.html",
            black_list=black_list, track_list=track_list, trackReg_list=trackReg_list, trackSet_list=trackSet_list,
            track_list_values=track_list_values, track_list_num_of_paste=track_list_num_of_paste,
            trackReg_list_values=trackReg_list_values, trackReg_list_num_of_paste=trackReg_list_num_of_paste,
            trackSet_list_values=trackSet_list_values, trackSet_list_num_of_paste=trackSet_list_num_of_paste,
            per_paste=per_paste, notificationEnabledDict=notificationEnabledDict, bootstrap_label=bootstrap_label,
            notificationEMailTermMapping=notificationEMailTermMapping, notificationTagsTermMapping=notificationTagsTermMapping)


@terms.route("/terms_management_query_paste/")
def terms_management_query_paste():
    term =  request.args.get('term')
    paste_info = []

    # check if regex or not
    if term.startswith('/') and term.endswith('/'):
        set_paste_name = "regex_" + term
        track_list_path = r_serv_term.smembers(set_paste_name)
    elif term.startswith('\\') and term.endswith('\\'):
        set_paste_name = "set_" + term
        track_list_path = r_serv_term.smembers(set_paste_name)
    else:
        set_paste_name = "tracked_" + term
        track_list_path = r_serv_term.smembers(set_paste_name)

    for path in track_list_path:
        paste = Paste.Paste(path)
        p_date = str(paste._get_p_date())
        p_date = p_date[0:4]+'/'+p_date[4:6]+'/'+p_date[6:8]
        p_source = paste.p_source
        p_size = paste.p_size
        p_mime = paste.p_mime
        p_lineinfo = paste.get_lines_info()
        p_content = paste.get_p_content()
        if p_content != 0:
            p_content = p_content[0:400]
        paste_info.append({"path": path, "date": p_date, "source": p_source, "size": p_size, "mime": p_mime, "lineinfo": p_lineinfo, "content": p_content})

    return jsonify(paste_info)


@terms.route("/terms_management_query/")
def terms_management_query():
    TrackedTermsDate_Name = "TrackedTermDate"
    BlackListTermsDate_Name = "BlackListTermDate"
    term =  request.args.get('term')
    section = request.args.get('section')

    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())
    value_range = Term_getValueOverRange(term, today_timestamp, [1, 7, 31])

    if section == "followTerm":
        term_date = r_serv_term.hget(TrackedTermsDate_Name, term)
    elif section == "blacklistTerm":
        term_date = r_serv_term.hget(BlackListTermsDate_Name, term)

    term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
    value_range.append(str(term_date))
    return jsonify(value_range)


@terms.route("/terms_management_action/", methods=['GET'])
def terms_management_action():
    today = datetime.datetime.now()
    today = today.replace(microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())


    section = request.args.get('section')
    action = request.args.get('action')
    term =  request.args.get('term')
    notificationEmailsParam = request.args.get('emailAddresses')
    input_tags = request.args.get('tags')

    if action is None or term is None or notificationEmailsParam is None:
        return "None"
    else:
        if section == "followTerm":
            if action == "add":

                # Make a list of all passed email addresses
                notificationEmails = notificationEmailsParam.split()

                validNotificationEmails = []
                # check for valid email addresses
                for email in notificationEmails:
                    # Really basic validation:
                    # has exactly one @ sign, and at least one . in the part after the @
                    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                        validNotificationEmails.append(email)

                # create tags list
                list_tags = input_tags.split()

                # check if regex/set or simple term
                #regex
                if term.startswith('/') and term.endswith('/'):
                    r_serv_term.sadd(TrackedRegexSet_Name, term)
                    r_serv_term.hset(TrackedRegexDate_Name, term, today_timestamp)
                    # add all valid emails to the set
                    for email in validNotificationEmails:
                        r_serv_term.sadd(TrackedTermsNotificationEmailsPrefix_Name + term, email)
                    # enable notifications by default
                    r_serv_term.sadd(TrackedTermsNotificationEnabled_Name, term)
                    # add tags list
                    for tag in list_tags:
                        r_serv_term.sadd(TrackedTermsNotificationTagsPrefix_Name + term, tag)
                    save_tag_to_auto_push(list_tags)

                #set
                elif term.startswith('\\') and term.endswith('\\'):
                    tab_term = term[1:-1]
                    perc_finder = re.compile("\[[0-9]{1,3}\]").search(tab_term)
                    if perc_finder is not None:
                        match_percent = perc_finder.group(0)[1:-1]
                        set_to_add = term
                    else:
                        match_percent = DEFAULT_MATCH_PERCENT
                        set_to_add = "\\" + tab_term[:-1] + ", [{}]]\\".format(match_percent)
                    r_serv_term.sadd(TrackedSetSet_Name, set_to_add)
                    r_serv_term.hset(TrackedSetDate_Name, set_to_add, today_timestamp)
                    # add all valid emails to the set
                    for email in validNotificationEmails:
                        r_serv_term.sadd(TrackedTermsNotificationEmailsPrefix_Name + set_to_add, email)
                    # enable notifications by default
                    r_serv_term.sadd(TrackedTermsNotificationEnabled_Name, set_to_add)
                    # add tags list
                    for tag in list_tags:
                        r_serv_term.sadd(TrackedTermsNotificationTagsPrefix_Name + set_to_add, tag)
                    save_tag_to_auto_push(list_tags)

                #simple term
                else:
                    r_serv_term.sadd(TrackedTermsSet_Name, term.lower())
                    r_serv_term.hset(TrackedTermsDate_Name, term.lower(), today_timestamp)
                    # add all valid emails to the set
                    for email in validNotificationEmails:
                        r_serv_term.sadd(TrackedTermsNotificationEmailsPrefix_Name + term.lower(), email)
                    # enable notifications by default
                    r_serv_term.sadd(TrackedTermsNotificationEnabled_Name, term.lower())
                    # add tags list
                    for tag in list_tags:
                        r_serv_term.sadd(TrackedTermsNotificationTagsPrefix_Name + term.lower(), tag)
                    save_tag_to_auto_push(list_tags)

            elif action == "toggleEMailNotification":
                # get the current state
                if term in r_serv_term.smembers(TrackedTermsNotificationEnabled_Name):
                    # remove it
                    r_serv_term.srem(TrackedTermsNotificationEnabled_Name, term.lower())
                else:
                    # add it
                    r_serv_term.sadd(TrackedTermsNotificationEnabled_Name, term.lower())

            #del action
            else:
                if term.startswith('/') and term.endswith('/'):
                    r_serv_term.srem(TrackedRegexSet_Name, term)
                    r_serv_term.hdel(TrackedRegexDate_Name, term)
                elif term.startswith('\\') and term.endswith('\\'):
                    r_serv_term.srem(TrackedSetSet_Name, term)
                    r_serv_term.hdel(TrackedSetDate_Name, term)
                else:
                    r_serv_term.srem(TrackedTermsSet_Name, term.lower())
                    r_serv_term.hdel(TrackedTermsDate_Name, term.lower())

                # delete the associated notification emails too
                r_serv_term.delete(TrackedTermsNotificationEmailsPrefix_Name + term)
                # delete the associated tags set
                r_serv_term.delete(TrackedTermsNotificationTagsPrefix_Name + term)

        elif section == "blacklistTerm":
            if action == "add":
                r_serv_term.sadd(BlackListTermsSet_Name, term.lower())
                r_serv_term.hset(BlackListTermsDate_Name, term, today_timestamp)
            else:
                r_serv_term.srem(BlackListTermsSet_Name, term.lower())
        else:
            return "None"

        to_return = {}
        to_return["section"] = section
        to_return["action"] = action
        to_return["term"] = term
        return jsonify(to_return)

@terms.route("/terms_management/delete_terms_tags", methods=['POST'])
def delete_terms_tags():
    term = request.form.get('term')
    tags_to_delete = request.form.getlist('tags_to_delete')

    if term is not None and tags_to_delete is not None:
        for tag in tags_to_delete:
            r_serv_term.srem(TrackedTermsNotificationTagsPrefix_Name + term, tag)
        return redirect(url_for('terms.terms_management'))
    else:
        return 'None args', 400

@terms.route("/terms_management/delete_terms_email", methods=['GET'])
def delete_terms_email():
    term =  request.args.get('term')
    email =  request.args.get('email')

    if term is not None and email is not None:
        r_serv_term.srem(TrackedTermsNotificationEmailsPrefix_Name + term, email)
        return redirect(url_for('terms.terms_management'))
    else:
        return 'None args', 400


@terms.route("/terms_plot_tool/")
def terms_plot_tool():
    term =  request.args.get('term')
    if term is not None:
        return render_template("terms_plot_tool.html", term=term)
    else:
        return render_template("terms_plot_tool.html", term="")


@terms.route("/terms_plot_tool_data/")
def terms_plot_tool_data():
    oneDay = 60*60*24
    range_start =  datetime.datetime.utcfromtimestamp(int(float(request.args.get('range_start')))) if request.args.get('range_start') is not None else 0;
    range_start = range_start.replace(hour=0, minute=0, second=0, microsecond=0)
    range_start = calendar.timegm(range_start.timetuple())
    range_end =  datetime.datetime.utcfromtimestamp(int(float(request.args.get('range_end')))) if request.args.get('range_end') is not None else 0;
    range_end = range_end.replace(hour=0, minute=0, second=0, microsecond=0)
    range_end = calendar.timegm(range_end.timetuple())
    term =  request.args.get('term')

    per_paste = request.args.get('per_paste')
    if per_paste == "1" or per_paste is None:
        per_paste = "per_paste_"
    else:
        per_paste = ""

    if term is None:
        return "None"

    else:
        value_range = []
        for timestamp in range(range_start, range_end+oneDay, oneDay):
            value = r_serv_term.hget(per_paste+str(timestamp), term)
            curr_value_range = int(value) if value is not None else 0
            value_range.append([timestamp, curr_value_range])
        value_range.insert(0,term)
        return jsonify(value_range)


@terms.route("/terms_plot_top/")
def terms_plot_top():
    per_paste = request.args.get('per_paste')
    per_paste = per_paste if per_paste is not None else 1
    return render_template("terms_plot_top.html", per_paste=per_paste)


@terms.route("/terms_plot_top_data/")
def terms_plot_top_data():
    oneDay = 60*60*24
    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())

    per_paste = request.args.get('per_paste')
    if per_paste == "1" or per_paste is None:
        per_paste = "per_paste_"
    else:
        per_paste = ""

    set_day = per_paste + "TopTermFreq_set_day_" + str(today_timestamp)
    set_week = per_paste + "TopTermFreq_set_week";
    set_month = per_paste + "TopTermFreq_set_month";

    the_set = per_paste + request.args.get('set')
    num_day = int(request.args.get('num_day'))

    if the_set is None:
        return "None"
    else:
        to_return = []
        if "TopTermFreq_set_day" in the_set:
            the_set += "_" + str(today_timestamp)

        for term, tot_value in r_serv_term.zrevrangebyscore(the_set, '+inf', '-inf', withscores=True, start=0, num=20):
            position = {}
            position['day'] = r_serv_term.zrevrank(set_day, term)
            position['day'] = position['day']+1 if position['day'] is not None else "<20"
            position['week'] = r_serv_term.zrevrank(set_week, term)
            position['week'] = position['week']+1 if position['week'] is not None else "<20"
            position['month'] = r_serv_term.zrevrank(set_month, term)
            position['month'] = position['month']+1 if position['month'] is not None else "<20"
            value_range = []
            for timestamp in range(today_timestamp, today_timestamp - num_day*oneDay, -oneDay):
                value = r_serv_term.hget(per_paste+str(timestamp), term)
                curr_value_range = int(value) if value is not None else 0
                value_range.append([timestamp, curr_value_range])

            to_return.append([term, value_range, tot_value, position])

        return jsonify(to_return)


@terms.route("/credentials_tracker/")
def credentials_tracker():
    return render_template("credentials_tracker.html")

@terms.route("/credentials_management_query_paste/", methods=['GET', 'POST'])
def credentials_management_query_paste():
    cred =  request.args.get('cred')
    allPath = request.json['allPath']

    paste_info = []
    for pathNum in allPath:
        path = r_serv_cred.hget(REDIS_KEY_ALL_PATH_SET_REV, pathNum)
        paste = Paste.Paste(path)
        p_date = str(paste._get_p_date())
        p_date = p_date[0:4]+'/'+p_date[4:6]+'/'+p_date[6:8]
        p_source = paste.p_source
        p_encoding = paste._get_p_encoding()
        p_size = paste.p_size
        p_mime = paste.p_mime
        p_lineinfo = paste.get_lines_info()
        p_content = paste.get_p_content()
        if p_content != 0:
            p_content = p_content[0:400]
        paste_info.append({"path": path, "date": p_date, "source": p_source, "encoding": p_encoding, "size": p_size, "mime": p_mime, "lineinfo": p_lineinfo, "content": p_content})

    return jsonify(paste_info)

@terms.route("/credentials_management_action/", methods=['GET'])
def cred_management_action():

    supplied =  request.args.get('term')
    action = request.args.get('action')
    section = request.args.get('section')
    extensive = request.args.get('extensive')
    extensive = True if extensive == "true" else False

    if extensive:
        #collectDico
        AllUsernameInRedis = r_serv_cred.hgetall(REDIS_KEY_ALL_CRED_SET).keys()
    uniq_num_set = set()
    if action == "seek":
        possibilities = mixUserName(supplied, extensive)
        for poss in possibilities:
            num = r_serv_cred.hget(REDIS_KEY_ALL_CRED_SET, poss)
            if num is not None:
                uniq_num_set.add(num)
            for num in r_serv_cred.smembers(poss):
                uniq_num_set.add(num)
        #Extensive /!\
        if extensive:
            iter_num = 0
            tot_iter = len(AllUsernameInRedis)*len(possibilities)
            for tempUsername in AllUsernameInRedis:
                for poss in possibilities:
                    #FIXME print progress
                    if(iter_num % int(tot_iter/20) == 0):
                        #print("searching: {}% done".format(int(iter_num/tot_iter*100)), sep=' ', end='\r', flush=True)
                        print("searching: {}% done".format(float(iter_num)/float(tot_iter)*100))
                    iter_num += 1

                    if poss in tempUsername:
                        num = (r_serv_cred.hget(REDIS_KEY_ALL_CRED_SET, tempUsername))
                        if num is not None:
                            uniq_num_set.add(num)
                        for num in r_serv_cred.smembers(tempUsername):
                            uniq_num_set.add(num)

    data = {'usr': [], 'path': [], 'numPaste': [], 'simil': []}
    for Unum in uniq_num_set:
        levenRatio = 2.0
        username = (r_serv_cred.hget(REDIS_KEY_ALL_CRED_SET_REV, Unum))

        # Calculate Levenshtein distance, ignore negative ratio
        supp_splitted = supplied.split()
        supp_mixed = supplied.replace(' ','')
        supp_splitted.append(supp_mixed)
        for indiv_supplied in supp_splitted:
            levenRatio = float(Levenshtein.ratio(indiv_supplied, username))
            levenRatioStr = "{:.1%}".format(levenRatio)

        data['usr'].append(username)


        allPathNum = list(r_serv_cred.smembers(REDIS_KEY_MAP_CRED_TO_PATH+'_'+Unum))

        data['path'].append(allPathNum)
        data['numPaste'].append(len(allPathNum))
        data['simil'].append(levenRatioStr)

    to_return = {}
    to_return["section"] = section
    to_return["action"] = action
    to_return["term"] = supplied
    to_return["data"] = data

    return jsonify(to_return)


# ========= REGISTRATION =========
app.register_blueprint(terms, url_prefix=baseUrl)

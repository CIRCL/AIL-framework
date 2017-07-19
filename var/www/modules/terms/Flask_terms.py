#!/usr/bin/env python2
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the trending modules page
'''
import redis
import datetime
import calendar
import flask
from flask import Flask, render_template, jsonify, request, Blueprint
import re
import Paste
from pprint import pprint
import Levenshtein

# ============ VARIABLES ============
import Flask_config

app = Flask_config.app
cfg = Flask_config.cfg
r_serv_term = Flask_config.r_serv_term
r_serv_cred = Flask_config.r_serv_cred

terms = Blueprint('terms', __name__, template_folder='templates')

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

def mixUserName(supplied):
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

    return usernames
 

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

    #Regex
    trackReg_list = []
    trackReg_list_values = []
    trackReg_list_num_of_paste = []
    for tracked_regex in r_serv_term.smembers(TrackedRegexSet_Name):
        trackReg_list.append(tracked_regex)
        value_range = Term_getValueOverRange(tracked_regex, today_timestamp, [1, 7, 31], per_paste=per_paste_text)

        term_date = r_serv_term.hget(TrackedRegexDate_Name, tracked_regex)

        set_paste_name = "regex_" + tracked_regex
        trackReg_list_num_of_paste.append(r_serv_term.scard(set_paste_name))
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        value_range.append(term_date)
        trackReg_list_values.append(value_range)

    #Set
    trackSet_list = []
    trackSet_list_values = []
    trackSet_list_num_of_paste = []
    for tracked_set in r_serv_term.smembers(TrackedSetSet_Name):
        trackSet_list.append(tracked_set)
        value_range = Term_getValueOverRange(tracked_set, today_timestamp, [1, 7, 31], per_paste=per_paste_text)

        term_date = r_serv_term.hget(TrackedSetDate_Name, tracked_set)

        set_paste_name = "set_" + tracked_set
        trackSet_list_num_of_paste.append(r_serv_term.scard(set_paste_name))
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        value_range.append(term_date)
        trackSet_list_values.append(value_range)

    #Tracked terms
    track_list = []
    track_list_values = []
    track_list_num_of_paste = []
    for tracked_term in r_serv_term.smembers(TrackedTermsSet_Name):
        track_list.append(tracked_term)
        value_range = Term_getValueOverRange(tracked_term, today_timestamp, [1, 7, 31], per_paste=per_paste_text)

        term_date = r_serv_term.hget(TrackedTermsDate_Name, tracked_term)

        set_paste_name = "tracked_" + tracked_term
        track_list_num_of_paste.append(r_serv_term.scard(set_paste_name))
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        value_range.append(term_date)
        track_list_values.append(value_range)


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
            per_paste=per_paste)


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
        p_date = p_date[6:]+'/'+p_date[4:6]+'/'+p_date[0:4]
        p_source = paste.p_source
        p_encoding = paste._get_p_encoding()
        p_size = paste.p_size
        p_mime = paste.p_mime
        p_lineinfo = paste.get_lines_info()
        p_content = paste.get_p_content().decode('utf-8', 'ignore')
        if p_content != 0:
            p_content = p_content[0:400]
        paste_info.append({"path": path, "date": p_date, "source": p_source, "encoding": p_encoding, "size": p_size, "mime": p_mime, "lineinfo": p_lineinfo, "content": p_content})

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
    if action is None or term is None:
        return "None"
    else:
        if section == "followTerm":
            if action == "add":
                # check if regex/set or simple term
                #regex
                if term.startswith('/') and term.endswith('/'):
                    r_serv_term.sadd(TrackedRegexSet_Name, term)
                    r_serv_term.hset(TrackedRegexDate_Name, term, today_timestamp)

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

                #simple term
                else:
                    r_serv_term.sadd(TrackedTermsSet_Name, term.lower())
                    r_serv_term.hset(TrackedTermsDate_Name, term.lower(), today_timestamp)
            #del action
            else:
                if term.startswith('/') and term.endswith('/'):
                    r_serv_term.srem(TrackedRegexSet_Name, term)
                    r_serv_term.hdel(TrackedRegexDate_Name, term)
                elif term.startswith('\\') and term.endswith('\\'):
                    r_serv_term.srem(TrackedSetSet_Name, term)
                    print(term)
                    r_serv_term.hdel(TrackedSetDate_Name, term)
                else:
                    r_serv_term.srem(TrackedTermsSet_Name, term.lower())
                    r_serv_term.hdel(TrackedTermsDate_Name, term.lower())

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

@terms.route("/credentials_management_query_paste/")
def credentials_management_query_paste():
    cred =  request.args.get('cred')
    return 1

   


@terms.route("/credentials_management_action/", methods=['GET'])
def cred_management_action():
    REGEX_CRED = '[a-z]+|[A-Z]{3,}|[A-Z]{1,2}[a-z]+|[0-9]+'
    REDIS_KEY_NUM_USERNAME = 'uniqNumForUsername'
    REDIS_KEY_NUM_PATH = 'uniqNumForUsername'
    REDIS_KEY_ALL_CRED_SET = 'AllCredentials'
    REDIS_KEY_ALL_CRED_SET_REV = 'AllCredentialsRev'
    REDIS_KEY_ALL_PATH_SET = 'AllPath'
    REDIS_KEY_ALL_PATH_SET_REV = 'AllPath'
    REDIS_KEY_MAP_CRED_TO_PATH = 'CredToPathMapping'

    supplied =  request.args.get('term').encode('utf-8')
    action = request.args.get('action')
    section = request.args.get('section')

    #splitedCred = re.findall(REGEX_CRED, cred)
    uniq_num_set = set()
    if action == "seek":
        possibilities = mixUserName(supplied)
        for poss in possibilities:
            for num in r_serv_cred.smembers(poss):
                uniq_num_set.add(num)

    data = {'usr': [], 'path': [], 'numPaste': [], 'simil': []}
    for Unum in uniq_num_set:
        username = r_serv_cred.hget(REDIS_KEY_ALL_CRED_SET_REV, Unum)
        
        # Calculate Levenshtein distance, ignore negative ratio
        levenDist = float(Levenshtein.distance(supplied, username))
        levenRatio = levenDist / float(len(supplied))
        levenRatioStr = "{:.1%}".format(1.0 - levenRatio)
        if levenRatio >= 1.0:
            continue

        data['usr'].append(username)
        data['path'].append(r_serv_cred.hget(REDIS_KEY_MAP_CRED_TO_PATH, Unum))
        data['numPaste'].append(len(uniq_num_set))
        data['simil'].append(levenRatioStr)

    to_return = {}
    to_return["section"] = section
    to_return["action"] = action
    to_return["term"] = supplied
    to_return["data"] = data

    return jsonify(to_return)


@terms.route("/credentials_management_query/")
def cred_management_query():
    return 1

# ========= REGISTRATION =========
app.register_blueprint(terms)

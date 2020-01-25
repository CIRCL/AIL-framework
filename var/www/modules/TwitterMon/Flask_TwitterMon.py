#!/usr/bin/env python3
# -*-coding:UTF-8 -*

#===========================================================================================================
# Author: Alfonso G. Alonso
# Twitter Monitor for AIL Framework
# For license information, see LICENSE.TXT
# ==========================================================================================================


# ========================================= FLASK_TWITTERMON ===============================================
#
#
# Interface between the TwitterMon settings page and the configuration file.
#
# Interface between the TwitterMon monitoring page and TweetsImporter.
#
# ==========================================================================================================

import redis
import TweetsImporter
from flask import Flask, render_template, jsonify, request, Blueprint
from flask_login import login_required
from pubsublogger import publisher
import configparser
import os

# =============================================================================
# =========================                 ===================================
# =========================   VARIABLES     ===================================
# =========================                 ===================================
# =============================================================================

import Flask_config

app = Flask_config.app
baseUrl = Flask_config.baseUrl
r_serv_TwAnalyzer = redis.StrictRedis(host="localhost",port="6382",db=10,decode_responses=True)
r_serv_TwTweets = redis.StrictRedis(host="localhost",port="6382",db=11,decode_responses=True)

publisher.port = 6380
publisher.channel = 'Script'

# TwitterMon configuration
TMconfigfile = os.path.join(os.environ['AIL_FLASK'], 'modules/TwitterMon/config/TwitterMon.cfg')
if not os.path.exists(TMconfigfile):
    raise Exception('Unable to find the TwitterMon')

TwitterMon = Blueprint('TwitterMon', __name__, template_folder='templates')

# =============================================================================
# =========================                 ===================================
# =========================   FUNCTIONS     ===================================
# =========================                 ===================================
# =============================================================================


# .............................................................................
# .......................                             .........................
# .......................  MONITORING FUNCTIONS       .........................
# .......................                             .........................
# .............................................................................
# .............................................................................


# .............................................................................
#
# ---------------------------------------
#  START MONITORING
# ---------------------------------------
#
# .............................................................................

@TwitterMon.route("/TwitterMon/start_monitoring")
def start_monitoring():
    searchName  = request.args.get('searchname')
    username  = request.args.get('username')
    terms  = request.args.get('terms')
    since  = request.args.get('since')
    until  = request.args.get('until')
    top  = request.args.get('top')
    maxT  = request.args.get('maxTweets')
    near  = request.args.get('near')
    within  = request.args.get('within')
    lang  = request.args.get('lang')
    
    TweetsImporter.manageMonitor("start","Monitor started user")
    TweetsImporter.monitorTweets(searchName,username,terms,since,until,top,maxT,near,within,lang)
    return "Done"


# .............................................................................
#
# ---------------------------------------
#  STOP MONITORING
# ---------------------------------------
#
# .............................................................................

@TwitterMon.route("/TwitterMon/stop_monitoring")
def stop_monitoring():
    TweetsImporter.manageMonitor("cancel","Cancelled by user")
    return "Done"


# .............................................................................
#
# ---------------------------------------
#  GET STATUS FUNCTIONS
# ---------------------------------------
#
# .............................................................................


@TwitterMon.route("/TwitterMon/get_Current_Search")
def get_Current_Search():
    return TweetsImporter.getCurrentSearch()

@TwitterMon.route("/TwitterMon/get_StatusDescription")
def get_StatusDescription():
    return TweetsImporter.getStatusDescription()


@TwitterMon.route("/TwitterMon/get_Status")
def get_Status():
    return TweetsImporter.getStatus()


@TwitterMon.route("/TwitterMon/get_Processing")
def get_Processing():
    return TweetsImporter.getProcessing()

@TwitterMon.route("/TwitterMon/get_Progress")
def get_Progress():
    return TweetsImporter.getProgress()


# .............................................................................
# .......................                             .........................
# .......................  REDIS ARDB FUNCTIONS       .........................
# .......................                             .........................
# .............................................................................
# .............................................................................

# .............................................................................
#
# ---------------------------------------
#  GET TWITTER SEARCHES
# ---------------------------------------
#
# .............................................................................

@TwitterMon.route("/TwitterMon/get_list_of_searches")
def get_list_of_searches():

    searches = []

    for currSearch in r_serv_TwAnalyzer.smembers('all_twitter_searches'):
        favorites = r_serv_TwAnalyzer.hget(str(currSearch),"favorites")
        tweets = r_serv_TwAnalyzer.hget(str(currSearch),"tweets")
        compound = r_serv_TwAnalyzer.hget(str(currSearch),"compound")
        minDate = r_serv_TwAnalyzer.hget(str(currSearch),"minDate")
        maxDate = r_serv_TwAnalyzer.hget(str(currSearch),"maxDate")
        retweets = r_serv_TwAnalyzer.hget(str(currSearch),"retweets")
        hashtags = r_serv_TwAnalyzer.hget(str(currSearch),"hashtags")
        hashtagsC = ""
        if hashtags != None:
                if ";" in hashtags:
                        hashtagsC = hashtags.replace(";","|-|")

        searches.append(currSearch + ";"+ str(tweets) + ";" + str(favorites) + ";" +str(compound)+ ";" +str(minDate)+ ";" +str(maxDate)+ ";" +str(retweets) + ";" +str(hashtagsC))

    return jsonify(searches)


# .............................................................................
#
# ---------------------------------------
#  GET GENERAL DATA FROM TWITTER SEARCH
# ---------------------------------------
#
# .............................................................................

@TwitterMon.route("/TwitterMon/get_twitter_search_general_data")
def get_twitter_search_general_data():

    searchName  = request.args.get('searchname')

    favorites = r_serv_TwAnalyzer.hget(searchName,"favorites")
    retweets = r_serv_TwAnalyzer.hget(searchName,"retweets")
    tweets = r_serv_TwAnalyzer.hget(searchName,"tweets")
    hashtags = r_serv_TwAnalyzer.hget(searchName,"hashtags")
    mentions = r_serv_TwAnalyzer.hget(searchName,"mentions")
    users = r_serv_TwAnalyzer.hget(searchName,"users")
    language = r_serv_TwAnalyzer.hget(searchName,"language")
    emojis = r_serv_TwAnalyzer.hget(searchName,"emojis")
    compound = r_serv_TwAnalyzer.hget(searchName,"compound")
    minDate = r_serv_TwAnalyzer.hget(searchName,"minDate")
    maxDate = r_serv_TwAnalyzer.hget(searchName,"maxDate")

    generalData = {'search':str(searchName),'tweets':str(tweets),'favorites':str(favorites),'retweets':str(retweets),'hashtags':str(hashtags),'mentions':str(mentions),'language':str(language),'emojis':str(emojis),'users':str(users),'compound':str(compound),'minDate':str(minDate),'maxDate':str(maxDate)}

    return generalData


# .............................................................................
#
# ---------------------------------------
#  GET TWEETS FROM TWITTER SEARCH
# ---------------------------------------
#
# .............................................................................

@TwitterMon.route("/TwitterMon/get_tweets_from_twitter_search")
def get_tweets_from_twitter_search():

    searchName  = request.args.get('searchname')
    tweets = r_serv_TwTweets.smembers(str(searchName))

    tweetsList = str(tweets)
    tweetsList = tweetsList.replace('}\'','}')
    tweetsList = tweetsList.replace('}"','}')
    tweetsList = tweetsList.replace('"{','{')
    tweetsList = tweetsList.replace('\'{','{')
    tweetsList = tweetsList.replace('{{','[{')
    tweetsList = tweetsList.replace('}}','}]')
    tweetsList = tweetsList.replace('"','\\"')
    tweetsList = tweetsList.replace('“','\\"')
    tweetsList = tweetsList.replace('”','\\"')
    tweetsList = tweetsList.replace('\\\'','"')
    tweetsList = tweetsList.replace('\'','"')
    return tweetsList



# .............................................................................
#
# ---------------------------------------
#  DELETE TWITTER SEARCH
# ---------------------------------------
#
# .............................................................................


@TwitterMon.route("/TwitterMon/delete_twitter_search_data")
def delete_twitter_search_data():

    searchName  = request.args.get('searchname')

    # Delete reference
    r_serv_TwAnalyzer.srem('all_twitter_searches',str(searchName))

    # Delete twitter search
    r_serv_TwAnalyzer.delete(str(searchName))

    # Delete tweets
    r_serv_TwTweets.delete(str(searchName))

    return "Done"


@TwitterMon.route("/TwitterMon/check_if_search_exists")
def check_if_search_exists():

    found = "False"
    searchName  = request.args.get('searchname')

    if (r_serv_TwAnalyzer.exists(searchName) == True):
        found = "True"

    return found



# .............................................................................
#
# ---------------------------------------
#  CHANGE TWEET TAG STATUS
# ---------------------------------------
#
# .............................................................................


@TwitterMon.route("/TwitterMon/changeTweetTag")
def changeTweetTag():
    result="Failure"	
    searchname  = request.args.get('searchname')
    tweetID  = str(request.args.get('tweetTag'))[4:]
    currValue = str(request.args.get('currValue'))
    if (currValue == "0"):
        oldValue = "'tagged': 0"
        newValue = "'tagged': 1"
    else:
        oldValue = "'tagged': 1"
        newValue = "'tagged': 0"

    for curr_tweet in r_serv_TwTweets.smembers(searchname):
        if (tweetID in curr_tweet):
            newTweet = str(curr_tweet).replace(oldValue,newValue)
            r_serv_TwTweets.srem(searchname,curr_tweet)
            r_serv_TwTweets.sadd(searchname,newTweet)
            result="Success"
            break
    return result





# .............................................................................
# .......................                             .........................
# .......................  CONFIGURATION MANAGEMENT   .........................
# .......................                             .........................
# .............................................................................
# .............................................................................



# .............................................................................
#
# ---------------------------------------
#  GET CONFIGURATION FROM FILE
# ---------------------------------------
#
# .............................................................................


@TwitterMon.route("/TwitterMon/get_configuration")
def get_configuration():

    cfgTM = configparser.ConfigParser()
    cfgTM.read(TMconfigfile)

    datavalue = str(cfgTM.get("TweetsImporter","real_time_max_time_backwards")) + ";" + str(cfgTM.get("TwitterAnalyzer","email_for_translation"))

    return datavalue


# .............................................................................
#
# ---------------------------------------
#  SAVE CONFIGURATION TO FILE
# ---------------------------------------
#
# .............................................................................

@TwitterMon.route("/TwitterMon/save_configuration")
def save_configuration():

    result = "Success."
    cfgTM = configparser.ConfigParser()
    cfgTM.read(TMconfigfile)

    parametersList = str(request.args.get('parameters')).split(";")
    maxTimeBW = parametersList[0]
    emailTrans = parametersList[1]

    try:
        cfgTM.set("TweetsImporter","real_time_max_time_backwards",maxTimeBW)
        cfgTM.set("TwitterAnalyzer","email_for_translation",emailTrans)
        with open(str(TMconfigfile), 'w') as configfile:
            cfgTM.write(configfile)
    except Exception as e:
        result = "Saving configuration failure: "+str(e)

    return result



	
# =============================================================================
# =========================                 ===================================
# =========================   ROUTES        ===================================
# =========================                 ===================================
# =============================================================================

#@TwitterMon.route("/TwitterMon/", methods=['GET']) AGACLEAN
@TwitterMon.route("/TwitterMon/")
@login_required
def TwitterMon_page():
    return render_template("TwitterMon.html")

#@TwitterMon.route("/TwitterMon/results_page", methods=['GET'])
@TwitterMon.route("/TwitterMon/results_page")
@login_required
def results_page():
    return render_template("TwitterMon_results.html")


@TwitterMon.route("/TwitterMon/settings_page")
@login_required
def settings_page():
    return render_template("TwitterMon_settings.html")

# ========= REGISTRATION =====================================================
app.register_blueprint(TwitterMon, url_prefix=baseUrl)


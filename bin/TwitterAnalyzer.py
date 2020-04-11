#!/usr/bin/env python3
# -*-coding:UTF-8 -*


# ==========================================================================================================
# Author: Alfonso G. Alonso
# Twitter Monitor for AIL Framework
# For license information, see LICENSE.TXT
# ==========================================================================================================


# ============================================ TWITTER ANALYZER ============================================
#
#
# 1- Receives tweets from queue
# 2- Creates Tweet class
# 3- Performs statistics 
# 4- Performs sentiment analysis
#
# ==========================================================================================================


import time
import datetime
import calendar
import redis
import json
import gzip
from pubsublogger import publisher
from Helper import Process
from packages import Tweet

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk import tokenize

# Config Variables
accepted_Mime_type = ['text/plain']
size_threshold = 250
line_max_length_threshold = 1000

import os
import configparser


# .............................................................................
#
#
#  ANALYSE TWEETS
# ---------------
#
# .............................................................................


def AnalyseTweets(message, serverTA, serverTT):

    path = message
    tweet = Tweet.Tweet(path)


    # CHECK IF MESSAGE IS A TWEET
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    # - Tweets published from TwitterMon start with [TM]-
    # - 

    if (tweet.publisherOr != "TwitterMon"):
        publisher.debug("[-TwitterAnalyzer-] AnalyseTweets. Discarding non-Tweet message")
        return

    # PROCESS TWEET
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    # - Extracts data from Tweet
    # - 

    tweet.process_Tweet()

 
    # STORE: SEARCH
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    # - Adds search to search list if not exists

    provider = tweet.t_TweetSource

    serverTA.sadd("all_twitter_searches",provider)


    # ANALYSE TWEET SENTENCES & STORE
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    # - Performs sentiment analysis
    # - Stores tweet

    resAddingTweet = AnalyseTweetSentences(tweet,serverTT,provider)

    if resAddingTweet == 0:
        publisher.info("[-TwitterAnalyzer-] Tweet already in DB, discarding")
        return
    #else:
    #    publisher.info("[-TwitterAnalyzer-] New tweet added.")

    #
    #  UPDATE TWITTER SEARCH STATISTICS
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    # Tweets, Retweets, Favorites
    # 
    serverTA.hincrby(provider,'tweets',1)
    serverTA.hincrby(provider,'retweets', tweet.get_Retweets())
    serverTA.hincrby(provider,'favorites', tweet.get_Favorites())
    
    # HashTags
    # 
    newHashTags = str(tweet.get_Hashtags()).strip()
    hashTags_list = newHashTags.split(' ')
    for hashTag in hashTags_list:
        if hashTag != "":
            serverTA.hset(provider,"hashtags",incrementValueForData(str(serverTA.hget(provider,'hashtags')),hashTag))

    # Mentions
    # 
    newMentions = str(tweet.get_Mentions()).strip()
    if newMentions != "":
        serverTA.hset(provider,"mentions",incrementValueForData(str(serverTA.hget(provider,'mentions')),newMentions))

    # Language
    # 
    newLanguage = str(tweet.get_Language()).strip()
    if newLanguage != "":
        serverTA.hset(provider,"language",incrementValueForData(str(serverTA.hget(provider,'language')),newLanguage))


    # Emojis
    # 
    newEmojis = str(tweet.get_Emojis()).strip()
    if newEmojis != "":
        serverTA.hset(provider,"emojis",incrementValueForData(str(serverTA.hget(provider,'emojis')),newEmojis))


    # User
    # 
    newUser = str(tweet.t_TweetUser).strip()
    if newUser != "":
        serverTA.hset(provider,"users",incrementValueForData(str(serverTA.hget(provider,'users')),newUser))


    # Min Date - Max Date
    #

    currMinDate = serverTA.hget(provider,'minDate')
    currMaxDate = serverTA.hget(provider,'maxDate')

    publisher.debug("Comparing new = "+str(tweet.t_TweetDate)+" with Min("+str(currMinDate)+") - Max("+str(currMaxDate)+")")
    if (currMinDate == None or (currMinDate > tweet.t_TweetDate)):
        publisher.info("New Min date")
        serverTA.hset(provider,"minDate",tweet.t_TweetDate)

    if (currMaxDate == None or (currMaxDate < tweet.t_TweetDate)):
        publisher.debug("New Max date")
        serverTA.hset(provider,"maxDate",tweet.t_TweetDate)

    # ANALYSE TWEET SENTENCES & STORE
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    # - Performs sentiment analysis
    # - Stores tweet

    #AnalyseTweetSentences(tweet,serverTT,provider)


    # STORE: ADD SENTIMENT OF TWEET TO GLOBAL SEARCH
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    # - 

    currPos = serverTA.hget(provider,"pos")
    currNeg = serverTA.hget(provider,"neg")
    currNeu = serverTA.hget(provider,"neu")
    currCompound = serverTA.hget(provider,"compound")
    currCompoundPos = serverTA.hget(provider,"compoundPos")
    currCompoundNeg = serverTA.hget(provider,"compoundNeg")

    if (currPos == None):
        currPos = 0
    if (currNeg == None):
        currNeg = 0
    if (currNeu == None):
        currNeu = 0
    if (currCompound == None):
        currCompound = 0
    if (currCompoundPos == None):
        currCompoundPos = 0
    if (currCompoundNeg == None):
        currCompoundNeg = 0

    publisher.debug("[-TwitterAnalyzer-] AnalyseTweets. Current sentiment. = pos: " + str(currPos) + " neg: "+str(currNeg)+ " neu: "+str(currNeu)+ " compound: "+str(currCompound)+" compoundPos: "+str(currCompoundPos)+" compoundNeg: "+str(currCompoundNeg))
    publisher.debug("[-TwitterAnalyzer-] AnalyseTweets. Adding sentiment. = pos: " + str(tweet.t_SentPos) + " neg: "+str(tweet.t_SentNeg)+ " neu: "+str(tweet.t_SentNeu)+ " compound: "+str(tweet.t_SentCompound)+" compoundPos: "+str(tweet.t_SentCompoundPos)+" compoundNeg: "+str(tweet.t_SentCompoundNeg))
    publisher.debug("[-TwitterAnalyzer-]  Checking New Pos "+str(tweet.t_SentPos)+" + Neg " + str(tweet.t_SentNeg) + " + Neu = "+ str(tweet.t_SentNeu) + "="+str(tweet.t_SentPos+tweet.t_SentNeg+tweet.t_SentNeu))


    prevTweets = int(serverTA.hget(provider,"tweets")) - 1
    numTweets = int(serverTA.hget(provider,"tweets"))
    #print("prevTweets = " + str(type(prevTweets)) + "currPos = " + str(type(currPos)) + "sentPos = "+str(type(tweet.t_SentPos)))
    publisher.debug("Operation for pos=("+str(float(currPos))+"*"+str(prevTweets)+")"+str(tweet.t_SentPos)+"/"+str(numTweets))
    newPos = ((float(currPos)*prevTweets) + tweet.t_SentPos)/numTweets
    newNeg = ((float(currNeg)*prevTweets) + tweet.t_SentNeg)/numTweets
    newNeu = ((float(currNeu)*prevTweets) + tweet.t_SentNeu)/numTweets
    newCompound = ((float(currCompound)*prevTweets) + tweet.t_SentCompound)/numTweets
    newCompoundPos = ((float(currCompoundPos)*prevTweets) + tweet.t_SentCompoundPos)/numTweets
    newCompoundNeg = ((float(currCompoundNeg)*prevTweets) + tweet.t_SentCompoundNeg)/numTweets

    serverTA.hset(provider,'pos',round(newPos,3))
    serverTA.hset(provider,'neg',round(newNeg,3))
    serverTA.hset(provider,'neu',round(newNeu,3))
    serverTA.hset(provider,'compound', round(newCompound,4))
    serverTA.hset(provider,'compoundNeg', round(newCompoundNeg,4))
    serverTA.hset(provider,'compoundPos', round(newCompoundPos,4))
    publisher.debug("[-TwitterAnalyzer-] AnalyseTweets. Updated sentiment. = pos: " + str(serverTA.hget(provider,"pos")) + " neg: "+str(serverTA.hget(provider,"neg"))+ " neu: "+str(serverTA.hget(provider,"neu"))+" compound: "+str(serverTA.hget(provider,"compound"))+ " compoundPos: "+str(serverTA.hget(provider,"compoundPos"))+" compoundNeg: "+str(serverTA.hget(provider,"compoundNeg")) + "numTweets = "+str(numTweets))




# .............................................................................
#
#
#  ANALYSE TWEET SENTENCES
#  -----------------------
#
# .............................................................................

def AnalyseTweetSentences(tweet,serverTT,provider):

    tweetText = tweet.t_TweetText
    tweetTextTrans = tweet.t_TweetTextTransEN
    tweetUser = tweet.t_TweetUser
    tweetId = tweet.t_TweetId
    tweetDate = tweet.t_TweetDate
    tweetLang = tweet.t_TweetLang


    # SELECT TEXT TO ANALYSE
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    # - If tweet is not in English, sentiment is performed to translation
    #

    sentences = ""
    if (tweetLang != "EN"):
        sentences = tokenize.sent_tokenize(tweetTextTrans)
    else:
        sentences = tokenize.sent_tokenize(tweetText)

    publisher.debug("[-TwitterAnalyzer-] AnalyseTweetSentiment, from user: " + tweetUser + " received = "+tweetText)


    # ANALYSE TWEET SENTENCES
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    # - Sentiment Analysis
    # - Stores tweet

    tweetText = tweetText.replace("\'","´")
    tweetTextTransEN = tweetTextTrans.replace("\'","´")

    tweet_processed = ""

    if len(sentences) > 0:
        tweet_processed = {'tweetID':str(tweetId),'tweetDate':str(tweetDate),'tweet':str(tweetText),'tweetTrans':str(tweetTextTransEN),'lang':str(tweetLang),'user':str(tweetUser),'tagged':0,'neg': 0.0, 'neu': 0.0, 'pos': 0.0,'compound': 0.0, 'compoundPos': 0.0, 'compoundNeg': 0.0}
        #tweet_processed = {"tweet":str(tweetText),"neg": 0.0, "neu": 0.0, "pos": 0.0, "compoundPos": 0.0, "compoundNeg": 0.0}
        neg_line = 0
        pos_line = 0
        num_line = 0

        analyzer = SentimentIntensityAnalyzer()
        
        for sentence in sentences:

            vs = analyzer.polarity_scores(str(sentence))
            #vs = analyzer.polarity_scores(str(sentence.encode('raw_unicode_escape').decode('utf8')))
            publisher.debug("AnalyseTweetSentiment, {:-<65} {}".format(sentence, str(vs)))

            for k in sorted(vs):
                if k == 'compound':
                    num_line += 1
                    tweet_processed['compound'] += vs[k]
                    if vs['neg'] > vs['pos']:
                        tweet_processed['compoundNeg'] += vs[k]
                        neg_line += 1
                    else:
                        tweet_processed['compoundPos'] += vs[k]
                        pos_line += 1
                else:
                    tweet_processed[k] += vs[k]

        for k in tweet_processed:
            if k == 'compoundPos':
                tweet_processed[k] = tweet_processed[k] / (pos_line if pos_line > 0 else 1)
            elif k == 'compoundNeg':
                tweet_processed[k] = tweet_processed[k] / (neg_line if neg_line > 0 else 1)
            elif k == 'compound':
                tweet_processed[k] = tweet_processed[k] / num_line
            elif (k == 'tweet' or k == 'user' or k == 'tweetID' or k == 'tweetDate' or k == 'tweetTrans' or k == 'tagged'or k == 'lang'):
                pass
            else:
                tweet_processed[k] = tweet_processed[k] / len(sentences)

        tweet.t_SentPos = round(tweet_processed['pos'],3)
        tweet.t_SentNeg = round(tweet_processed['neg'],3)
        tweet.t_SentNeu = round(tweet_processed['neu'],3)
        tweet.t_SentCompound = round(tweet_processed['compound'],4)
        tweet.t_SentCompoundPos = round(tweet_processed['compoundPos'],4)
        tweet.t_SentCompoundNeg = round(tweet_processed['compoundNeg'],4)

        #publisher.info("[-TwitterAnalyzer-] AnalyseTweetSentiment, pos: " + str(tweet_processed['pos']) + " neg: "+str(tweet_processed['neg'])+ " neu: "+str(tweet_processed['neu'])+ " compoundPos: "+str(tweet_processed['compoundPos'])+" compoundNeg: "+str(tweet_processed['compoundNeg']))
        added = serverTT.sadd(provider, tweet_processed)

        return added


# .............................................................................
#
#
#  AUX FUNCTION: Incremente value
#  -------------------------------
#
#  currData = "es(x22);en(x3)"  (valueToIncr="es")-> "es(x23);en(x3)"
# .............................................................................

def incrementValueForData(currData,valueToIncr):

    newData = currData	
    pos = currData.find(valueToIncr)
    if pos != -1:
        posStartNumber = currData.rfind("x",pos)
        posCloseBracket = currData.rfind(")",pos)
        count = currData[posStartNumber+1:posCloseBracket]

        newCount = int(count) + 1

        prevDataText = valueToIncr + "(x" + str(count) + ")"
        newDataText = valueToIncr + "(x" + str(newCount) + ")"

        newData = currData.replace(prevDataText,newDataText)
    else:
        if (currData != None and currData != "None"):
            newData = currData + ";" + valueToIncr + "(x1)"
        else:
            newData = valueToIncr + "(x1)"
    #publisher.info("[-TwitterAnalyzer-] incrementValueForData,currData = " + currData +" received = " + valueToIncr + " newData = "+newData)

    return newData

def isJSON(content):
    try:
        json.loads(content)
        return True

    except Exception:
        return False






import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)



# .............................................................................
#
#
#  MAIN
#  -------------------
#
# .............................................................................


if __name__ == '__main__':


    # LOG: CONFIGURE PUBLISHER
    # ----------------------------------------------------

    publisher.port = 6380
    publisher.channel = 'Script'


    # REDIS QUEUE: CONFIGURE ACCESS TO MESSAGES QUEUE
    # ----------------------------------------------------

    # Section name in bin/packages/modules.cfg
    config_section = 'TwitterAnalyzer'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Script Twitter Sentiment Analysis started")


    # DATABASES: CONFIGURE DATABASES
    # ----------------------------------------------------

    # DB FOR TWITTER ANALYSIS
    serverTA = redis.StrictRedis(host="localhost",port="6382",db=10,decode_responses=True)
    serverTT = redis.StrictRedis(host="localhost",port="6382",db=11,decode_responses=True)

    #serverTA = redis.StrictRedis(
    #	host=p.config.get("ARDB_TwitterAnalyzer", "host"),
    #	port=p.config.get("ARDB_TwitterAnalyzer", "port"),
    #	db=p.config.get("ARDB_TwitterAnalyzer", "db"),
    #	decode_responses=True)


    # DB FOR TWEETS

    #serverTT = redis.StrictRedis(
    #	host=p.config.get("ARDB_TwitterTweets", "host"),
    #	port=p.config.get("ARDB_TwitterTweets", "port"),
    #	db=p.config.get("ARDB_TwitterTweets", "db"),
    #	decode_responses=True)


    # INFINITE LOOP: Wait for messages, process.
    # ----------------------------------------------------

    time1 = time.time()

    while True:
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue
        signal.alarm(60)
        try:

            # Send for analysis
            # ----------------------------------------------------
            AnalyseTweets(message, serverTA, serverTT)

        except TimeoutException:
            p.incr_module_timeout_statistic()
            print ("{0} processing timeout".format(message))
            continue
        else:
            signal.alarm(0)

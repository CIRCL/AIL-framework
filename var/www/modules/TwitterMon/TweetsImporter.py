#!/usr/bin/env python3
# -*-coding:UTF-8 -*

#===========================================================================================================
# Author: Alfonso G. Alonso
# Twitter Monitor for AIL Framework
# For license information, see LICENSE.TXT
# ==========================================================================================================


# ========================================= TWEETS IMPORTER ===============================================
#
#
# Retrieves Tweets from Twitter based on query received
#
# Injects tweets collected in AIL Framework
#
# The module can be executed from terminal with the following parameters:
#
#     username: Username of a specific twitter account (without @)
#     since: The lower bound date (yyyy-mm-aa)
#     until: The upper bound date (yyyy-mm-aa)
#     querysearch: A query text to be matched
#     near: A reference location area from where tweets were generated
#     within: A distance radius from "near" location (e.g. 15mi)
#     maxtweets: The maximum number of tweets to retrieve
#     toptweets: Only the tweets provided as top tweets by Twitter (no parameters required)
#     
# Example:
#     python TweetsImporter.py --username "barcelona" --maxtweets 1
#
# ==========================================================================================================

import sys,getopt,time,datetime,codecs,os,shutil,gzip,zmq,base64,json,re,logging
import TM_Status
import urllib.request as urllib2
import http.cookiejar as cookielib
from bs4 import BeautifulSoup, Tag

from pyquery import PyQuery

# TwitterMon configuration
#

import configparser
import os
TMconfigfile = os.path.join(os.environ['AIL_FLASK'], 'modules/TwitterMon/config/TwitterMon.cfg')
if not os.path.exists(TMconfigfile):
    raise Exception('Unable to find the TwitterMon')


class Tweet:
	
	def __init__(self):
		pass

class TweetCriteria:
	
	def __init__(self):
		self.maxTweets = 0
		self.within = "15mi"
		
	def setUsername(self, username):
		self.username = username
		return self
		
	def setSince(self, since):
		self.since = since
		return self
	
	def setUntil(self, until):
		self.until = until
		return self
		
	def setQuerySearch(self, querySearch):
		self.querySearch = querySearch
		return self

	def setMaxTweets(self, maxTweets):
		self.maxTweets = maxTweets
		return self

	def setTopTweets(self, topTweets):
		self.topTweets = topTweets
		return self
	
	def setNear(self, near):
		self.near = near
		return self

	def setLang(self, lang):
		self.lang = lang
		return self

	def setWithin(self, within):
		self.within = within
		return self

# ===========================================================================================================================================
# ===========================================================================================================================================
# ====================================              FUNCTIONS                 ===============================================================
# ===========================================================================================================================================
# ===========================================================================================================================================




# .............................................................................
#
#
#  GETTWEETS
# ---------------
#
# .............................................................................

class TweetsManager:

	@staticmethod
	def getTweets(tweetCriteria, receiveBuffer=None, bufferLength=100, proxy=None):

		TM_Status.refreshCursor = ''
		TM_Status.results = []
		TM_Status.resultsAux = []

		cookieJar = cookielib.CookieJar()
		
		if hasattr(tweetCriteria, 'username') and (tweetCriteria.username.startswith("\'") or tweetCriteria.username.startswith("\"")) and (tweetCriteria.username.endswith("\'") or tweetCriteria.username.endswith("\"")):
			tweetCriteria.username = tweetCriteria.username[1:-1]

		active = True
		cancelled = False
		empty = False

		# GET TWEETS WHILE ACTIVE
		# --------------------------------------------------------------------------

		while active:

			# CHECK IF CANCELLED BY USER
			# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
			# - Exit from while to not process more tweets

			#TMLogger('TwitterMon').info("Checking order ="+TM_Status.currentorder)
			if (TM_Status.currentorder != "start"):
				active = False
				cancelled = True
				break


			# INFORM
			# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
			#

			if (TM_Status.refreshCursor == ""):
				manageStatus("working","Starting new request","")

			# REQUEST ->  <-- JSON
			# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
			#

			json = TweetsManager.getJsonReponse(tweetCriteria, TM_Status.refreshCursor, cookieJar, proxy)


			# CHECK RESPONSE
			# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

			# NOTHING RECEIVED
			#
			if (len(json['items_html'].strip()) == 0):

				if (TM_Status.realTimeMode == False):
					active = False
					empty = True
					if receiveBuffer and len(TM_Status.resultsAux) >= 0:
						TMLogger('TwitterMon').info("Nothing found in las request, sending tweets in buffer")
						tmpResults = TM_Status.resultsAux
						receiveBuffer(tmpResults)
						TM_Status.resultsAux = []
				else:
					manageStatus("working","Real-time monitoring: Nothing found, waiting...","")
					TM_Status.refreshCursor = ''
					time.sleep(4)

			# DATA RECEIVED
			#

			else:
				TweetsManager.processResponse(json)

				if (TM_Status.realTimeMode == True and TM_Status.TweetsTooOld):
					TM_Status.TweetsTooOld = False
					TMLogger('TwitterMon').info("Gone too far in time, returning to present")
					manageStatus("working","Gone too far in time, returning to present to find new Tweets","")
					if (receiveBuffer and len(TM_Status.resultsAux) > 0):
						manageStatus("working","Gone too far in time, meanwhile sending already received","")
						tmpResults = TM_Status.resultsAux
						receiveBuffer(tmpResults)
						TM_Status.resultsAux = []
						TM_Status.results = []
					time.sleep(4)
					refreshCursor = ''

				if receiveBuffer and len(TM_Status.resultsAux) >= bufferLength:
					tmpResults = TM_Status.resultsAux
					receiveBuffer(tmpResults)
					TM_Status.resultsAux = []

				if (TM_Status.maximumReached):
					active = False
				

		# CHECK EXIT REASON
		# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
		#
		TMLogger('TwitterMon').info("TweetsManager: active="+str(active))

		if cancelled == False and empty == False and TM_Status.maximumReached == False and receiveBuffer and len(TM_Status.resultsAux) > 0:
			TMLogger('TwitterMon').info("TI [TweetsManager]: What is this situation")
			tmpResults = TM_Status.resultsAux
			receiveBuffer(tmpResults)
		elif empty == True:
			if (TM_Status.progress == 0):
				logMessage = "No tweets found"
			else:
				logMessage = "No more tweets found."
			TMLogger('TwitterMon').info("TI [TweetsManager]: " +logMessage)
			manageStatus("finished",logMessage,"")
			#return
		elif TM_Status.maximumReached == True:
			TMLogger('TwitterMon').info("TI [TweetsManager]: Maximum tweets sent. Quit.")
			manageStatus("finished","Maximum tweets sent.","")
			#return
		elif cancelled == True:
			TMLogger('TwitterMon').info("TI [TweetsManager]: Cancelled by user. Quit.")
			manageStatus("cancelled","Cancelled by user. Exit.","")
		else:
			TMLogger('TwitterMon').error("TI [TweetsManager]: Unexpected state.")

		#TMLogger('TwitterMon').info("TweetsManager: end function, returning: "+str(TM_Status.results))
		#return TM_Status.results



# .............................................................................
#
#
#  PROCESS RESPONSE
# ---------------
#
# .............................................................................


	@staticmethod
	def processResponse(json):

		TM_Status.refreshCursor = json['min_position']

		# PROCES JSON RECEVIED
		# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

		##
		# Remove incomplete tweets withheld by Twitter Guidelines
		##			

		scrapedTweets = PyQuery(json['items_html'])
		scrapedTweets.remove('div.withheld-tweet')
		tweets = scrapedTweets('div.js-stream-tweet')
			

		# TWEETS LEFT? 
		# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
		# Check if there are still tweets after processing

		#if len(tweets) == 0:
		#	manageStatus("finished","No more tweets found","")
		#	break


		# Inform
		# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
			
		manageStatus("working","Response received, analyzing Tweets","")
		currTweet = 0

		for tweetHTML in tweets:

			# CHECK IF CANCELLED BY USER
			# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

			#TMLogger('TwitterMon').info("Checking order before processing = "+TM_Status.currentorder)
			#if (TM_Status.currentorder != "start"):
			#	active = False
			#	cancelled = True
			#	break

			# PROCESS TWEET DATA
			# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

			tweetPQ = PyQuery(tweetHTML)

			# GET USERNAME
			#
			usernameTweet = tweetPQ("span:first.username.u-dir b").text()

			# GET NUMBER OF RETWEETS AND FAVORITES
			#
			retweets = int(tweetPQ("span.ProfileTweet-action--retweet span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""))
			favorites = int(tweetPQ("span.ProfileTweet-action--favorite span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""))

			# GET TIME
			#
			dateSec = int(tweetPQ("small.time span.js-short-timestamp").attr("data-time"))

			# GET TWEET LANGUAGE
			#
			lang = str(tweetPQ("p.js-tweet-text").attr("lang"))

			# GET TWEET ID & PERMALINK
			#
			id = tweetPQ.attr("data-tweet-id")
			permalink = tweetPQ.attr("data-permalink-path")

			# GET GEO
			#
			geo = ''
			geoSpan = tweetPQ('span.Tweet-geo')
			if len(geoSpan) > 0:
				geo = geoSpan.attr('title')


			# PREPARE TWEET TEXT
			# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

			#TMLogger('TwitterMon').info("Received RAW text = " + str(tweetPQ))

			soupTweet = BeautifulSoup(str(tweetPQ),'lxml')

			##
			# CLEAN EMOJI'S TAGS
			##

			emojis = ''
			for imgE in soupTweet.findAll('img'):
				try:
					if (str(imgE['class']).find("Emoji") != -1):	
						emojis += imgE['alt']                    #Also store all emojis
						imgE.replaceWith(str(imgE['alt']))
				except KeyError:
					pass
			##
			# CLEAN TEXT
			##

			txtTweetClean = ''				
			for txtTweetTmp in soupTweet.findAll('p'):
				try:
					if (str(txtTweetTmp['class']).find("js-tweet-text") != -1):	
						txtTweetClean += str(txtTweetTmp)
				except KeyError:
					pass

			tweetPQTweetClean = PyQuery(txtTweetClean)
			txtTweet = re.sub(r"\s+", " ", tweetPQTweetClean("p.js-tweet-text").text().replace('# ', '#').replace('@ ', '@'))				


			# FIX MENTIONS AND HASHTAGS

			txtTweetAt = txtTweet.replace("@ ","@")
			txtTweetHash = txtTweetAt.replace("# ","#")
			txtTweetSemicolon = txtTweetHash.replace(";",",")
			txtTweetOpBracks = txtTweetSemicolon.replace("{","\\{")
			txtTweetCloseBracks = txtTweetOpBracks.replace("}","\\}")
			txtTweetOpCol = txtTweetCloseBracks.replace("[","\\[")
			txtTweetCloseCol = txtTweetOpCol.replace("]","\\]")
			txtTweetCooked = txtTweetCloseCol

			# STORE TWEET DATA
			# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

			tweet = Tweet()
			tweet.id = id
			tweet.permalink = 'https://twitter.com' + permalink
			tweet.username = usernameTweet
			tweet.text = txtTweetCooked
			tweet.emojis = emojis
			tweet.date = datetime.datetime.fromtimestamp(dateSec)
			tweet.retweets = retweets
			tweet.favorites = favorites
			tweet.mentions = " ".join(re.compile('(@\\w*)').findall(tweet.text))
			tweet.hashtags = " ".join(re.compile('(#\\w*)').findall(tweet.text))
			tweet.geo = geo
			tweet.lang = lang

			TMLogger('TwitterMon').info("## -- Tweet proceses ------------------ ")
			TMLogger('TwitterMon').info("## TweetId =" + str(tweet.id))
			TMLogger('TwitterMon').info("## Tweet Permalink =" + str(tweet.permalink))
			TMLogger('TwitterMon').info("## Tweet Username =" + str(tweet.username))
			TMLogger('TwitterMon').info("## Tweet Text =" + tweet.text)
			TMLogger('TwitterMon').info("## Tweet Emojis =" + tweet.emojis)
			TMLogger('TwitterMon').info("## Tweet Date =" + str(tweet.date))
			TMLogger('TwitterMon').info("## Tweet Retweets =" + str(tweet.retweets))
			TMLogger('TwitterMon').info("## Tweet Favorites =" + str(tweet.favorites))
			TMLogger('TwitterMon').info("## Tweet Mentions =" + str(tweet.mentions))
			TMLogger('TwitterMon').info("## Tweet Hashtags =" + str(tweet.hashtags))
			TMLogger('TwitterMon').info("## Tweet Geo =" + str(tweet.geo))
			TMLogger('TwitterMon').info("## Tweet Lang =" + str(tweet.lang))
			TMLogger('TwitterMon').info("## ------------------------------------- ")

				
			# REAL-TIME OUTDATED CHECK
			# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
			# Check if 1st Tweet in block is too outdated for Real-Time

			currTweet += 1
			dateF = "%Y-%m-%d %H:%M:%S"
			now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			diffSec = datetime.datetime.strptime(str(now),dateF) - datetime.datetime.strptime(str(tweet.date),dateF)
			#TMLogger('TwitterMon').info("Tweet Time = "+str(tweet.date)+ " Start time = " + str(now) + " difference = "+str(diffSec.total_seconds()))

			if (TM_Status.realTimeMode == True):
				if (diffSec.total_seconds() > TM_Status.maxTimeBW):
					TM_Status.TweetsTooOld = True
					break

				
			# APPEND RESULTS
			# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

			TM_Status.results.append(tweet)
			TM_Status.resultsAux.append(tweet)



# .............................................................................
#
#
#  GETRESPONSE
# ---------------
#
# .............................................................................
	
	@staticmethod
	def getJsonReponse(tweetCriteria, refreshCursor, cookieJar, proxy):

		if hasattr(tweetCriteria, 'lang'):
			url = "https://twitter.com/i/search/timeline?f=tweets&q=%s&l="+tweetCriteria.lang+"&src=typd&max_position=%s"
		else:
			url = "https://twitter.com/i/search/timeline?f=tweets&q=%s&src=typd&max_position=%s"

		urlGetData = ''
		
		if hasattr(tweetCriteria, 'username'):
			urlGetData += ' from:' + tweetCriteria.username
		
		if hasattr(tweetCriteria, 'querySearch'):
			urlGetData += ' ' + tweetCriteria.querySearch
		
		if hasattr(tweetCriteria, 'near'):
			urlGetData += "&near:" + tweetCriteria.near + " within:" + tweetCriteria.within
		
		if hasattr(tweetCriteria, 'since'):
			urlGetData += ' since:' + tweetCriteria.since
			
		if hasattr(tweetCriteria, 'until'):
			urlGetData += ' until:' + tweetCriteria.until

		if hasattr(tweetCriteria, 'topTweets'):
			if tweetCriteria.topTweets:
				url = "https://twitter.com/i/search/timeline?q=%s&src=typd&max_position=%s"
		
		url = url % (urllib2.quote(urlGetData), urllib2.quote(refreshCursor))

		headers = [
			('Host', "twitter.com"),
			('User-Agent', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"),
			('Accept', "application/json, text/javascript, */*; q=0.01"),
			('Accept-Language', "de,en-US;q=0.7,en;q=0.3"),
			('X-Requested-With', "XMLHttpRequest"),
			('Referer', url),
			('Connection', "keep-alive")
		]

		if proxy:
			opener = urllib2.build_opener(urllib2.ProxyHandler({'http': proxy, 'https': proxy}), urllib2.HTTPCookieProcessor(cookieJar))
		else:
			opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
		opener.addheaders = headers

		try:
			TMLogger('TwitterMon').info('Trying url'+url)
			response = opener.open(url)
			jsonResponse = response.read().decode('utf-8')
		except:
			manageStatus("error","Twitter weird response or timeout received.","")
			TMLogger('TwitterMon').error("Twitter weird response. Try to see on browser: https://twitter.com/search?q=%s&src=typd" % urllib2.quote(urlGetData))
			return
		
		TMLogger('TwitterMon').debug("Response received: "+str(jsonResponse))
		dataJson = json.loads(jsonResponse)
	
		return dataJson


# .............................................................................
#
#
#  LOGGING
# ---------------
#
# .............................................................................

loggers = {}

def TMLogger(name):

	global loggers

	if loggers.get(name):
		return loggers.get(name)
	else:
		logsFolder = os.environ['AIL_HOME']+"/var/www/modules/TwitterMon/logs/"

		if not os.path.exists(logsFolder):
			os.makedirs(logsFolder)
		else:
			os.remove(logsFolder+'TwitterMon.log')

		logger = logging.getLogger('TwitterMon')
		hdlr = logging.FileHandler(logsFolder+'TwitterMon.log')
		formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		hdlr.setFormatter(formatter)
		logger.addHandler(hdlr) 
		logger.setLevel(logging.INFO)
		loggers[name] = logger

		return logger	




# .............................................................................
#
#
#  MAIN
# ---------------
#
# .............................................................................

def main(argv):

	username=""
	query=""
	since=""
	until=""
	topTweets=""
	maxTweets=""
	near=""
	within=""
	lang=""

	opts, args = getopt.getopt(argv, "", ("username=", "near=", "within=", "since=", "until=", "querysearch=", "toptweets", "maxtweets=", "lang="))

	for opt,arg in opts:
		if opt == '--username':
			username = arg

		elif opt == '--since':
			since = arg

		elif opt == '--until':
			until = arg

		elif opt == '--querysearch':
			query = arg

		elif opt == '--toptweets':
			topTweets = "True"

		elif opt == '--maxtweets':
			maxTweets = arg

		elif opt == '--near':
			near = arg

		elif opt == '--within':
			within = arg

		elif opt == '--lang':
			within = arg

	manageMonitor("start","Monitor started from main")
	monitorTweets("default",username,query,since,until,topTweets,maxTweets,near,within)


# .............................................................................
#
#
#  MANAGE MONITOR
# ---------------
#
# ............................................................................

def manageMonitor(action,description):

	# MANAGE ORDER
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	
	if (action == "cancel"):
		TM_Status.currentorder = "cancel"
		TMLogger('TwitterMon').info("# ORDER >>> Cancel " + description)
		TMLogger('TwitterMon').info("# ------------------------------ ")

	elif (action == "start"):
		TM_Status.currentorder = "start"
		TMLogger('TwitterMon').info("# ------------------------------ ")
		TMLogger('TwitterMon').info("# ORDER >>> Start " + description)

		cfgTM = configparser.ConfigParser()
		cfgTM.read(TMconfigfile)
		TM_Status.maxTimeBW = int(cfgTM.get("TweetsImporter","real_time_max_time_backwards"))
		TMLogger('TwitterMon').info("# TM_Status.maxTimeBW =  " + str(TM_Status.maxTimeBW))
	else:
		TMLogger('TwitterMon').error('Unexpected action '+action+' for manageMonitor\n')
		return


# .............................................................................
#
#
#  MANAGE MONITOR
# ---------------
#
# ............................................................................

def manageStatus(newStatus,description,processing):

	# MANAGE STATE
	# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	
	closeSocket = False
	exitTM = False
	if (newStatus == "working"):

		TM_Status.lastLogProgress += 1
		if (TM_Status.progress > 0):
			TM_Status.processing = "Sending Tweet " + str(TM_Status.progress) + ": " + processing

		if ((newStatus == TM_Status.status) and (TM_Status.statusDescription == description)):
			if (TM_Status.lastLogProgress > 100):
				TM_Status.lastLogProgress = 0
				TMLogger('TwitterMon').info('Monitor working: ['+str(TM_Status.progress)+'/'+str(TM_Status.maxTweets)+']')
				TMLogger('TwitterMon').info(' |-'+description + ' processing: '+processing)
		else:		
			TM_Status.status = "working"
			TM_Status.statusDescription = description
			TMLogger('TwitterMon').info('Monitor working: ['+str(TM_Status.progress)+'/'+str(TM_Status.maxTweets)+']')
			TMLogger('TwitterMon').info(' |-'+description + ' processing: '+processing)

	elif (newStatus == "finished"):
		TM_Status.status = "finished"
		TM_Status.statusDescription = description
		TMLogger('TwitterMon').info('Monitor finished:'+description)
		closeSocket = True
		exitTM = True
	elif (newStatus == "error"):
		TM_Status.status = "error"
		TM_Status.statusDescription = description
		TMLogger('TwitterMon').info('Error:'+description)
		closeSocket = True
		exitTM = True
	elif (newStatus == "cancelled"):
		TM_Status.status = "cancelled"
		TM_Status.currentorder = "cancelled"
		TM_Status.statusDescription = description
		TMLogger('TwitterMon').info(description)
		closeSocket = True
		exitTM = True
	else:
		TMLogger('TwitterMon').error('Unexpected status '+newStatus+' for manageStatus\n')
		return

	if (closeSocket == True):
		try:
			TM_Status.socket.close()
			TMLogger('TwitterMon').info('Socket closed')
		except Exception as e:
			TMLogger('TwitterMon').error('Error closing socket: '+str(e))
			quit()

	if (exitTM == True):
		TMLogger('TwitterMon').info('TI [manageStatus] << << EXIT >> >> Au revoir')


# .............................................................................
#
#
#  RETURN STATUS
# ---------------
#
# ............................................................................

def getStatusDescription():
	return TM_Status.statusDescription

def getStatus():
	return TM_Status.status

def getProcessing():
	return TM_Status.processing

def getProgress():
	return str(TM_Status.progress)

def getCurrentSearch():
	return str(TM_Status.currentSearch)

# .............................................................................
#
#
#  MONITOR TWEETS
# ---------------
#
# ............................................................................


def monitorTweets(nameForBlock,username,query,since,until,topTweets,maxTweets,near,within,lang):


	# LOG REQUEST
	# -----------------------------------------------------------------------

	currSearch = "Current search: "
	if (query != ""): currSearch += " Query: " + query
	if (username != ""): currSearch += " Username: " + username
	if (since != ""): currSearch += " Since: " + since
	if (until != ""): currSearch += " Until: " + until
	if (topTweets != ""): currSearch += " TopTweets: " + topTweets
	if (maxTweets != ""): currSearch += " Maximum: " + maxTweets
	if (near != ""): currSearch += " Near: " + near
	if (within != ""): currSearch += " Within: " + within
	if (lang != ""): currSearch += " Language: " + lang
	TM_Status.currentSearch = currSearch

	# CONTROL EARLY CANCEL
	# -----------------------------------------------------------------------

	if (TM_Status.currentorder != "start"):
		manageStatus("cancelled","Cancelled by user. Quitting.","")
		quit()
		return

	# LOG REQUEST
	# -----------------------------------------------------------------------

	manageStatus("working","Request received: nameForBlock = " + nameForBlock + " username = " + username + "terms = " + query + "since = " + since + " until = " + until + "topTweets = " + topTweets + "maxTweets = " + maxTweets + "near = " + near + "within = " + within + "language = "+lang, "")

	# REAL TIME MODE?
	# -----------------------------------------------------------------------

	if (since == "" and until ==""):
		TM_Status.realTimeMode = True
		TMLogger('TwitterMon').info(" @ > Real-time mode: on ")
	else:
		TM_Status.realTimeMode = False
		TMLogger('TwitterMon').info(" @ > Real-time mode: off ")


	# OUTPUT FOLDER
	# -----------------------------------------------------------------------
		
	outputFolder = os.environ['AIL_HOME']+"/var/www/modules/TwitterMon/data"

	if not os.path.exists(outputFolder):
		os.makedirs(outputFolder)

	# CLEAR DATA FOLDER
	try:
		shutil.rmtree(outputFolder+"/")
	except:
		manageStatus("error","Error removing output folder","")
		TMLogger('TwitterMon').error("Error while deleting directory")
		return


	# UPDATE STATE AND LOG
	# -----------------------------------------------------------------------

	manageStatus("working","Searching for tweets ...","")

	# RESET COUNTER
	# -----------------------------------------------------------------------
	TM_Status.progress = 0
	TM_Status.maximumReached = False

	if (maxTweets.strip() == ""):
		TM_Status.maxTweets = -1
	else:
		TM_Status.maxTweets = int(maxTweets.strip())


	# TWEET CRITERIA CLASS
	# -----------------------------------------------------------------------
	tweetCriteria = TweetCriteria()

	toptweets = topTweets.lower()

	if (username.strip() != ""): tweetCriteria.username = username.strip()
	if (query.strip() != ""): tweetCriteria.querySearch = query.strip()
	if (since.strip() != ""): tweetCriteria.since = since.strip()
	if (until.strip() != ""): tweetCriteria.until = until.strip()
	if (maxTweets.strip() != ""): tweetCriteria.maxTweets = int(maxTweets.strip())
	if (topTweets.strip() == "True"): tweetCriteria.topTweets = True
	if (near.strip() != ""): tweetCriteria.near = '"' + near.strip() + '"'
	if (within.strip() != ""): tweetCriteria.within = '"' + within.strip() + '"'
	if (lang.strip() != ""): tweetCriteria.lang = lang.strip()

	TMLogger('TwitterMon').info('Tweet criteria created')

	# ZMQ SOCKET
	# -----------------------------------------------------------------------

	try:
		context = zmq.Context()
		TM_Status.socket = context.socket(zmq.PUB)
		TM_Status.socket.bind("tcp://*:5556")
		TMLogger('TwitterMon').info('Connected to socket')
		time.sleep(1) #Important, avoid loosing the 1 message

	except Exception as e:
		manageStatus("error","Socket error: "+str(e),"")
		TMLogger('TwitterMon').error("Socket error: "+str(e))
		return


	# PROCESS BLOCK RECEIVED
	# -----------------------------------------------------------------------

	def receiveBuffer(tweets):
		
		# CHECK IF CANCELLED
		# - - - - - - - - - - - - - - - - - - -

		if (TM_Status.currentorder != "start"):
			manageStatus("cancelled","Cancelled by user. Quitting.","")
			quit()
			return

		# INCREASE BLOCK COUNT
		# - - - - - - - - - - - - - - - - - - -

		global blockCount
		blockCount += 1
		tweetNum = 0

		# CREATE FOLDER FOR THIS BLOCK
		# - - - - - - - - - - - - - - - - - - -

		if (nameForBlock=="default"):
			outputPath = outputFolder+"/[TM]-block-"+str(blockCount)+"/"
		else:
			outputPath = outputFolder+"/[TM]-" + nameForBlock+"/"

		TMLogger('TwitterMon').info('Starting block with number of tweets = ' + str(len(tweets)))

		for t in tweets:

			tweetNum += 1
			ignoreRepeated = False

			# CHECK IF CANCELLED
			# - - - - - - - - - - - - - - - - - - -

			if (TM_Status.currentorder != "start"):
				manageStatus("cancelled","Cancelled by user while processing tweet" + str(tweetNum) + " in block "+ str(blockCount),"")
				break

			# PREPARE FILE'S PATHS
			# ---------------------------------------------------

			tweetYear = t.date.strftime("%Y")
			tweetMonth = t.date.strftime("%m")
			tweetDay = t.date.strftime("%d")

			pathForTweet = outputPath+tweetYear+"/"+tweetMonth+"/"+tweetDay
                                
			if not os.path.exists(pathForTweet):
				os.makedirs(pathForTweet)

			fullPath = pathForTweet + "/" + t.username + "-" + t.date.strftime("%Y-%m-%d-%s")+".txt"
			fullPathGZ = pathForTweet + "/" + t.username + "-" + t.date.strftime("%Y-%m-%d-%s")+".txt.gz"

			# CHECK IF TWEET ALREADY DOWNLOADED
			# ---------------------------------------------------
			# It may occur in the time-loop of real-time mode

			if (TM_Status.realTimeMode == True):
				if (os.path.exists(fullPathGZ)):
					ignoreRepeated = True
					TMLogger('TwitterMon').debug("Already downloaded")
					continue
			
			# CREATE FILE
			# ---------------------------------------------------
                         
			tweetFile = codecs.open(fullPath, "w+", "utf-8")
			
			# UPDATE STATE AND LOG
			# ---------------------------------------------------

			tweetFile.flush()
			tweetFile.write(('%s;%s;%d;%d;%s;%s;%s;%s;%s;%s;%s;"%s"' % (t.username, t.date.strftime("%Y-%m-%d %H:%M"), t.retweets, t.favorites, t.text, t.geo, t.mentions, t.hashtags, t.id, t.permalink,t.lang,t.emojis)))

			tweetFile.close()

			# CHECK AND READ
			# ---------------------------------------------------

			with open(fullPath, 'rb') as f_in:
			    messagedata = f_in.read()
			    #TMLogger('TwitterMon').info("Message Data read="+str(messagedata.decode('utf-8')))

			#TODO
			#os.remove(fullPath)

			# INCREASE COUNTER			
			TM_Status.progress += 1

			# SEND TO ZMQ
			path_to_send = "TwitterMon" + '>>' + fullPathGZ
			channel = '102'

			s = b' '.join( [channel.encode(), path_to_send.encode(), base64.b64encode(gzip.compress(messagedata)) ] )
			TM_Status.socket.send(s)

			tweetLog = t.date.strftime("%Y-%m-%d %H:%M") + " " + t.text
			#TMLogger('TwitterMon').info("Sent tweet "+str(TM_Status.progress))
			manageStatus("working","Processing Tweet",tweetLog)

			time.sleep(0.25)


			# DISCARD IF MAXIMUM TWEETS REACHED
			# ---------------------------------------------------
			# Mark and exit loop

			if ((TM_Status.maxTweets != -1) and (TM_Status.progress >= TM_Status.maxTweets)):
				TMLogger('TwitterMon').info("Maximum reached, marked")
				TM_Status.maximumReached = True
				break


		# UPDATE STATE AND LOG
		# ------------------------------------------------------------
		# Leave TM_Status as it could have been cancelled or finished

		TMLogger('TwitterMon').info('End of for in receiveBuffer')
		#if ((TM_Status.maxTweets != -1) and (TM_Status.progress >= TM_Status.maxTweets)):
		#	manageStatus("finished","Max tweets reached","")


		#manageStatus(TM_Status.status,"Block "+str(blockCount)+" processed in "+outputPath+" with "+str(len(tweets))+"tweets","")		
			
	TweetsManager.getTweets(tweetCriteria, receiveBuffer)


if __name__ == 'TweetsImporter':
	blockCount = 0

if __name__ == '__main__':
	blockCount = 0
	main(sys.argv[1:])


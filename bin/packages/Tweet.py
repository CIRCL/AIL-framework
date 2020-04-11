#!/usr/bin/python3

# ==========================================================================================================
# Author: Alfonso G. Alonso
# Twitter Monitor for AIL Framework
# For license information, see LICENSE.TXT
# ==========================================================================================================


# ============================================ TWEET CLASS =================================================
#
#
# Creates a Tweet object from a tweet retrieved from TweetsImporter.
#
#
# ==========================================================================================================


import os
import gzip
import redis
import re
import configparser
import sys
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
from Date import Date
from pubsublogger import publisher
from langid.langid import LanguageIdentifier, model
from nltk.tokenize import RegexpTokenizer
from textblob import TextBlob

# TwitterMon configuration
TMconfigfile = os.path.join(os.environ['AIL_FLASK'], 'modules/TwitterMon/config/TwitterMon.cfg')
if not os.path.exists(TMconfigfile):
    raise Exception('Unable to find the TwitterMon')

try:
    sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
    import ConfigLoader
except:
    print("Can't import ConfigLoader")

# Translation Request
import requests
import json

#clean = lambda dirty: ''.join(filter(string.printable.__contains__, dirty))
#"""It filters out non-printable characters from the string it receives."""


class Tweet(object):

   # .............................................................................
   #
   #  MAIN
   #  -------------------
   #
   # .............................................................................


    def __init__(self, p_path):
        try:
            config_loader = ConfigLoader.ConfigLoader()
            self.PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes"))
            if self.PASTES_FOLDER not in p_path:
                self.p_rel_path = p_path
                self.p_path = os.path.join(self.PASTES_FOLDER, p_path)
                self.t_clean_path = p_path.replace('//', '/', 1)
            else:
                self.p_path = p_path
                self.p_rel_path = p_path.replace(self.PASTES_FOLDER+'/', '', 1)
                self.t_clean_path = p_path.replace('//', '/', 1)
        except:
            configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
            if not os.path.exists(configfile):
                raise Exception('Unable to find the configuration file. \
                            Did you set environment variables? \
                            Or activate the virtualenv.')

            cfg = configparser.ConfigParser()
            cfg.read(configfile)

            self.PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], cfg.get("Directories", "pastes"))
            if self.PASTES_FOLDER not in p_path:
                self.p_rel_path = p_path
                self.p_path = os.path.join(self.PASTES_FOLDER, p_path)
                self.t_clean_path = p_path.replace('//', '/', 1)
            else:
                self.p_path = p_path
                self.p_rel_path = p_path.replace(self.PASTES_FOLDER+'/', '', 1)
                self.t_clean_path = p_path.replace('//', '/', 1)

	#---	
        self.p_path = self.t_clean_path
        self.p_name = os.path.basename(self.p_path)
        self.p_size = round(os.path.getsize(self.p_path)/1024.0, 2)
        #self.p_mime = magic.from_buffer("test", mime=True)
        #self.p_mime = magic.from_buffer(self.get_p_content(), mime=True)

        # Assuming that the paste will alway be in a day folder which is itself
        # in a month folder which is itself in a year folder.
        # /year/month/day/paste.gz

        var = self.p_path.split('/')
        self.p_date = Date(var[-4], var[-3], var[-2])
        self.p_date_path = os.path.join(var[-4], var[-3], var[-2], self.p_name)


        self.p_encoding = None
        self.p_hash_kind = {}
        self.p_hash = {}
        self.p_langage = None
        self.p_nb_lines = None
        self.p_max_length_line = None
        self.array_line_above_threshold = None
        self.p_duplicate = None
        self.p_tags = None

        #
        #  PROVIDER - SEARCH
        #  -------------------

        tmpTweetSource = var[-5]
        cleanTweetSource = tmpTweetSource
        publisherOr = "UND"
        if (str(tmpTweetSource).find("[TM]-") == 0):
                cleanTweetSource = tmpTweetSource[5:]
                publisherOr = "TwitterMon"

        self.t_TweetSource = cleanTweetSource
        self.publisherOr = publisherOr
        #self.supposed_url = 'https://{}/{}'.format(self.t_TweetSource.replace('_pro', ''), var[-1].split('.gz')[0])

        #
        #  TWEET DATA
        #  -------------------

        self.t_TweetRaw = None
        self.t_TweetUser = None
        self.t_TweetDate = None
        self.t_TweetRetweets = 0
        self.t_TweetFavorites = 0
        self.t_TweetText = None
        self.t_TweetTextTransEN = None
        self.t_TweetGeo = None
        self.t_TweetMentions = None
        self.t_TweetHashTags = None
        self.t_TweetId = None
        self.t_TweetPermalink = None
        self.t_TweetLang = None
        self.t_TweetLangGuess = None
        self.t_TweetEmojis = None
        self.t_SentPos = None
        self.t_SentNeg = None
        self.t_SentNeu = None
        self.t_SentCompound = None
        self.t_SentCompoundNeg = None
        self.t_SentCompoundPos = None

   # .............................................................................
   #
   #
   #  PROCESS TWEET
   #  -------------------
   #
   # .............................................................................

    def process_Tweet(self):

        publisher.port = 6380
        publisher.channel = 'Script'

	# Get Tweet RAW content
	# ---------------------

        tweetRaw = self.get_TweetRawContent()
        self.t_TweetRaw = tweetRaw
        #publisher.debug("[-Tweet.py-] (process_Tweet) Raw Text = " + self.t_TweetRaw)

        tweetData = tweetRaw.split(";")

        #for data in tweetData:
        #    publisher.debug("[-Tweet.py-] data = "+data)

	# Assign data to Tweet
	# ---------------------

        self.t_TweetUser = tweetData[0].replace("b'\\n", "", 1)
        self.t_TweetDate = tweetData[1]
        self.t_TweetRetweets = int(tweetData[2])
        self.t_TweetFavorites = int(tweetData[3])
        self.t_TweetText = tweetData[4]
        self.t_TweetGeo = tweetData[5]
        self.t_TweetMentions = tweetData[6]
        self.t_TweetHashTags = tweetData[7]
        self.t_TweetId = int(tweetData[8])
        self.t_TweetPermalink = tweetData[9]
        self.t_TweetLang = tweetData[10].strip().upper()
        self.t_TweetEmojis = tweetData[11]

	# Translate Tweet if necessary
	# ----------------------------

	##
	# Try to guess language if not known
	##

        if (self.t_TweetLang == "und"):
                identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
                self.t_TweetLangGuess = identifier.classify(self.t_TweetText)[0]

	##
	# Translate if not in English
	##

        self.t_TweetTextTransEN = "Not necessary. Already in English"
        if (self.t_TweetLang.upper() != "EN"):
                fromLang = self.t_TweetLang
                if (self.t_TweetLang == "und"):
                        fromLang = self.t_TweetLangGuess

                publisher.debug("[-Tweet.py-] (process_Tweet) Trans necessary for"+self.t_TweetLang);
                self.t_TweetTextTransEN = self.translateTweet(self.t_TweetText,fromLang)

#        identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
#        return identifier.classify(self.get_p_content())

        publisher.debug("[-Tweet.py-] (process_Tweet) -------------------------------------------------------------")
        publisher.debug("[-Tweet.py-] (process_Tweet) from source " + self.t_TweetSource)
        publisher.debug("[-Tweet.py-] (process_Tweet) from publisher " + self.publisherOr)
        publisher.debug("[-Tweet.py-] (process_Tweet) Retweets = " + str(self.t_TweetRetweets))
        publisher.debug("[-Tweet.py-] (process_Tweet) Favorites = " + str(self.t_TweetFavorites))
        publisher.debug("[-Tweet.py-] (process_Tweet) User " + self.t_TweetUser)
        publisher.debug("[-Tweet.py-] (process_Tweet) Date " + self.t_TweetDate)
        publisher.debug("[-Tweet.py-] (process_Tweet) Geo " + self.t_TweetGeo)
        publisher.debug("[-Tweet.py-] (process_Tweet) Mentions = " + self.t_TweetMentions)
        publisher.debug("[-Tweet.py-] (process_Tweet) HashTags " + self.t_TweetHashTags)
        publisher.debug("[-Tweet.py-] (process_Tweet) Id " + str(self.t_TweetId))
        publisher.debug("[-Tweet.py-] (process_Tweet) Permalink " + self.t_TweetPermalink)
        #publisher.debug("[-Tweet.py-] (process_Tweet) Text " + self.t_TweetText)
        #publisher.debug("[-Tweet.py-] (process_Tweet) Text translated " + self.t_TweetTextTransEN)
        publisher.debug("[-Tweet.py-] (process_Tweet) Lang " + self.t_TweetLang)
        publisher.debug("[-Tweet.py-] (process_Tweet) LangGuess " + str(self.t_TweetLangGuess))
        publisher.debug("[-Tweet.py-] (process_Tweet) Emojis " + self.t_TweetEmojis)
        publisher.debug("[-Tweet.py-] (process_Tweet) -------------------------------------------------------------")

        #publisher.debug("[-Tweet.py-] data = " + self.t_TweetUser + " - " + self.t_TweetDate + " - " + str(self.t_TweetRetweets) + " - " + str(self.t_TweetFavorites) + " - " + self.t_TweetText + " - " + self.t_TweetGeo + " - " + self.t_TweetMentions + " - " + self.t_TweetHashTags + " - " + self.t_TweetId + " - " + self.t_TweetPermalink)

        #return str(tweetRaw)

   # .............................................................................
   #
   #
   #  GET TWEET RAW CONTENT
   #  -------------------
   #
   # .............................................................................


    def get_TweetRawContent(self):

        publisher.port = 6380
        publisher.channel = 'Script'
        #publisher.debug("[-Tweet.py-] Requested RAW Content = " + self.p_path)
        tweetRaw = ''

        #publisher.debug("[-Tweet.py-] Reading file " + self.p_path)
        #print("[-Tweet.py-] Reading file " + self.p_path)
        try:
            with gzip.open(self.p_path, 'rb') as f:
                tweetRaw = f.read().decode('utf-8')
        except Exception as e:
            publisher.debug("error opening path: "+self.p_path + " with error "+str(e))
            paste = 'error opening path: '+self.p_path + ' with error '+str(e)

        return str(tweetRaw)


   # .............................................................................
   #
   #
   #  GET RETWEETS
   #  -------------------
   #
   # ............................................................................

    def get_Retweets(self):
        return self.t_TweetRetweets


   # .............................................................................
   #
   #
   #  GET FAVORITES
   #  -------------------
   #
   # ............................................................................

    def get_Favorites(self):
        return self.t_TweetFavorites



   # .............................................................................
   #
   #
   #  GET HASHTAGS
   #  -------------------
   #
   # ............................................................................

    def get_Hashtags(self):
        TweetHashTags = ""
        if self.t_TweetHashTags != None:
                TweetHashTags = self.t_TweetHashTags 
        return TweetHashTags


   # .............................................................................
   #
   #
   #  GET MENTIONS
   #  -------------------
   #
   # ............................................................................

    def get_Mentions(self):
        TweetMentions = ""
        if self.t_TweetMentions != None:
                TweetMentions = self.t_TweetMentions 
        return TweetMentions


   # .............................................................................
   #
   #
   #  GET LANGUAGE
   #  -------------------
   #
   # ............................................................................

    def get_Language(self):
        TweetLanguage = ""
        if self.t_TweetLang != None:
                TweetLanguage = self.t_TweetLang 
        return TweetLanguage



   # .............................................................................
   #
   #
   #  GET EMOJIS
   #  -------------------
   #
   # ............................................................................

    def get_Emojis(self):
        TweetEmojis = ""
        if self.t_TweetEmojis != None:
                TweetEmojis = self.t_TweetEmojis 
        return TweetEmojis



   # .............................................................................
   #
   #
   #  TRANSLATE SENTENCE
   #  -------------------
   #
   # ............................................................................

    def translateTweet(self,sentence,from_lang):

        publisher.debug("[-Tweet.py-] (translateTweet) Request from "+from_lang.upper())


        re.sub("#|@|&","",sentence)
        cfgTM = configparser.ConfigParser()
        cfgTM.read(TMconfigfile)
        emailforTranslation = cfgTM.get("TwitterAnalyzer", "email_for_translation")

        api_url = "http://mymemory.translated.net/api/get?q={}&langpair={}|{}&de={}".format(sentence,from_lang.upper(),"EN",emailforTranslation)
        hdrs = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}

        publisher.debug("[-Tweet.py-] (translateTweet) Request url="+api_url) 
        response = requests.get(api_url, headers=hdrs)
        response_json = json.loads(response.text)
        translation = response_json["responseData"]["translatedText"]
        return translation



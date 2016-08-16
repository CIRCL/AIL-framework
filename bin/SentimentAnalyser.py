#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
    Sentiment analyser module.
    It takes its inputs from 'shortLine' and 'longLine'.
    Source code is taken into account (in case of comments). If it is only source code,
    it will be treated with a neutral value anyway.

nltk.sentiment.vader module:
    Hutto, C.J. & Gilbert, E.E. (2014). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. Eighth International Conference on Weblogs and Social Media (ICWSM-14). Ann Arbor, MI, June 2014.

"""

import time
import datetime
import calendar
import redis
import json
from pubsublogger import publisher
from Helper import Process
from packages import Paste

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import tokenize

# Config Variables
accepted_Mime_type = ['text/plain']

def Analyse(message, server):
    #print 'analyzing'
    path = message
    paste = Paste.Paste(path)

    content = paste.get_p_content()
    provider = paste.p_source
    p_date = str(paste._get_p_date())
    p_MimeType = paste._get_p_encoding()

    # Perform further analysis
    if p_MimeType == "text/plain":
        if isJSON(content):
            p_MimeType = "JSON"

    if p_MimeType in accepted_Mime_type:
        print 'Processing', path
        the_date = datetime.date(int(p_date[0:4]), int(p_date[4:6]), int(p_date[6:8]))
        #print 'pastedate: ', the_date
        the_time = datetime.datetime.now()
        the_time = datetime.time(getattr(the_time, 'hour'), 0, 0)
        #print 'now: ', the_time
        combined_datetime = datetime.datetime.combine(the_date, the_time)
        #print 'combined: ', combined_datetime
        timestamp = calendar.timegm(combined_datetime.timetuple())
        #print 'timestamp: ', timestamp 
    
        sentences = tokenize.sent_tokenize(content.decode('utf-8', 'ignore'))
        #print len(sentences)
    
        avg_score = {'neg': 0.0, 'neu': 0.0, 'pos': 0.0, 'compoundPos': 0.0, 'compoundNeg': 0.0}
        neg_line = 0
        pos_line = 0
        sid = SentimentIntensityAnalyzer()
        for sentence in sentences:
             ss = sid.polarity_scores(sentence)
             for k in sorted(ss):
                 if k == 'compound':
                     if ss['neg'] > ss['pos']:
                         avg_score['compoundNeg'] += ss[k]
                         neg_line += 1
                     else:
                         avg_score['compoundPos'] += ss[k]
                         pos_line += 1
                 else:
                     avg_score[k] += ss[k]
    
                 #print('{0}: {1}, '.format(k, ss[k]))
    
        for k in avg_score:
            if k == 'compoundPos':
                avg_score[k] = avg_score[k] / (pos_line if pos_line > 0 else 1)
            elif k == 'compoundNeg':
                avg_score[k] = avg_score[k] / (neg_line if neg_line > 0 else 1)
            else:
                avg_score[k] = avg_score[k] / len(sentences)
    
    
        # In redis-levelDB: {} = set, () = K-V 
        # {Provider_set -> provider_i}
        # {Provider_TimestampInHour_i -> UniqID_i}_j
        # (UniqID_i -> PasteValue_i)
    
        server.sadd('Provider_set', provider)
        #print 'Provider_set', provider
    
        provider_timestamp = provider + '_' + str(timestamp)
        #print provider_timestamp
        server.incr('UniqID')
        UniqID = server.get('UniqID')
        print provider_timestamp, '->', UniqID
        server.sadd(provider_timestamp, UniqID)
        server.set(UniqID, avg_score)
        print avg_score
        #print UniqID, '->', avg_score
    else:
        print 'Dropped:', p_MimeType
    

def isJSON(content):
    try:
        json.loads(content)
        return True

    except Exception,e:
        return False

if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'SentimentAnalysis'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("<description of the module>")

    # REDIS_LEVEL_DB #
    server = redis.StrictRedis(
        host=p.config.get("Redis_Level_DB_Sentiment", "host"),
        port=p.config.get("Redis_Level_DB_Sentiment", "port"),
        db=p.config.get("Redis_Level_DB_Sentiment", "db"))

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        Analyse(message, server)

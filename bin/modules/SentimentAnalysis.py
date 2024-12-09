#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    Sentiment analyser module.
    It takes its inputs from 'global'.

    The content is analysed if the length of the line is
    above a defined threshold (get_p_content_with_removed_lines).
    This is done because NLTK sentences tokemnizer (sent_tokenize) seems to crash
    for long lines (function _slices_from_text line#1276).


    nltk.sentiment.vader module credit:
        Hutto, C.J. & Gilbert, E.E. (2014). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. Eighth International Conference on Weblogs and Social Media (ICWSM-14). Ann Arbor, MI, June 2014.

"""

##################################
# Import External packages
##################################
import os
import sys
import time
import datetime
import calendar
import redis
import json
import signal
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import tokenize, download

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Items import Item
from lib import ConfigLoader


class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

## TODO: REFACTOR MODULE + CLEAN HISTORY
class SentimentAnalysis(AbstractModule):
    """
    SentimentAnalysis module for AIL framework
    """

    # Config Variables
    accepted_Mime_type = ['text/plain']
    line_max_length_threshold = 1000

    def __init__(self):
        super(SentimentAnalysis, self).__init__()

        self.sentiment_lexicon_file = ConfigLoader.ConfigLoader().get_config_str("Directories", "sentiment_lexicon_file")

        # REDIS_LEVEL_DB #
        self.db = ConfigLoader.ConfigLoader().get_redis_conn("_Sentiment")

        self.time1 = time.time()

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 1

        # Send module state to logs
        self.logger.info(f"Module {self.module_name} initialized")

    def compute(self, message):
        # Max time to compute one entry
        signal.alarm(60)
        try:
            self.analyse(message)
        except TimeoutException:
            self.logger.debug(f"{message} processing timeout")
        else:
            signal.alarm(0)

    def get_p_content_with_removed_lines(self, threshold, item_content):
        num_line_removed = 0
        line_length_threshold = threshold
        string_content = ""
        f = item_content
        for line_id, line in enumerate(f):
            length = len(line)

            if length < line_length_threshold:
                string_content += line
            else:
                num_line_removed += 1

        return num_line_removed, string_content

    def analyse(self, message):

        item = Item(message)

        # get content with removed line + number of them
        num_line_removed, p_content = self.get_p_content_with_removed_lines(SentimentAnalysis.line_max_length_threshold,
                                                                            item.get_content())
        provider = item.get_source()
        p_date = item.get_date()
        p_MimeType = item.get_mimetype()

        # Perform further analysis
        if p_MimeType == "text/plain":
            if self.isJSON(p_content):
                p_MimeType = "JSON"

        if p_MimeType in SentimentAnalysis.accepted_Mime_type:
            self.logger.debug(f'Accepted :{p_MimeType}')

            the_date = datetime.date(int(p_date[0:4]), int(p_date[4:6]), int(p_date[6:8]))
            the_time = datetime.datetime.now()
            the_time = datetime.time(getattr(the_time, 'hour'), 0, 0)
            combined_datetime = datetime.datetime.combine(the_date, the_time)
            timestamp = calendar.timegm(combined_datetime.timetuple())

            try:
                sentences = tokenize.sent_tokenize(p_content)
            except:
                # use the NLTK Downloader to obtain the resource
                download('punkt')
                sentences = tokenize.sent_tokenize(p_content)

            if len(sentences) > 0:
                avg_score = {'neg': 0.0, 'neu': 0.0, 'pos': 0.0, 'compoundPos': 0.0, 'compoundNeg': 0.0}
                neg_line = 0
                pos_line = 0
                sid = SentimentIntensityAnalyzer(self.sentiment_lexicon_file)
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

                self.db.sadd('Provider_set', provider)

                provider_timestamp = provider + '_' + str(timestamp)
                self.db.incr('UniqID')
                UniqID = self.db.get('UniqID')
                self.logger.debug(f'{provider_timestamp}->{UniqID}dropped{num_line_removed}lines')
                self.db.sadd(provider_timestamp, UniqID)
                self.db.set(UniqID, avg_score)
        else:
            self.logger.debug(f'Dropped:{p_MimeType}')


    def isJSON(self, content):
        try:
            json.loads(content)
            return True

        except Exception:
            return False


if __name__ == '__main__':

    module = SentimentAnalysis()
    module.run()

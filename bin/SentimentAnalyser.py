#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
    Template for new modules

nltk.sentiment.vader module:
    Hutto, C.J. & Gilbert, E.E. (2014). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. Eighth International Conference on Weblogs and Social Media (ICWSM-14). Ann Arbor, MI, June 2014.

"""

import time
from pubsublogger import publisher
from Helper import Process

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk import tokenize


def Analyse(message):
    path = message
    paste = Paste.paste(path)
    content = paste.p_get_content()

    sentences = tokenize.sent_tokenize(content.decode('utf-8', 'ignore'))
    
    sid = SentimentIntensityAnalyzer()
    for sentence in sentences:
         print(sentence)
         ss = sid.polarity_scores(sentence)
         for k in sorted(ss):
             print('{0}: {1}, '.format(k, ss[k]))
         print ''

if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = '<section name>'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("<description of the module>")

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        Analyse(message)

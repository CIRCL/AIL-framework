#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
	Module for specific text analysis
	More global aim would be to detect an attempt of: Ransom, Phishing, Social Engineering, etc.
	Here, only ENGLISH words, and related to Ransoms/Ransomwares are sought for now.
	When this module will run smoothly and give results, it'll be a good framework for other threatening Pastes (phishing, dox, skids, etc.)

	Module's format:
	- analyse whether the content is in natural human language ( <-- ignored, we actually check every Paste)
	- a file "AIL-framework/nltk_data/corpora/dict/ransom.dic" lists keywords and their (arbitrary) weight
	- keep a local var dict_ransom["word": weight]
	- tested texts are lowercased
	- compare the text and look for the keywords from "dict_ransom"
	- add the weight of those keywords in a "counter" variable (representing the probability of an actual threatining ransom)
	- ignore repetitions (otherwise, "database" would increase N times the counter, even if it has a weight of 1 and is barely relevant)
	- raise an alert only if the threat of an actual ransom message is higher than an (arbitrary) threshold
"""

import time
import pprint
from packages import Paste
from packages import lib_refine
from pubsublogger import publisher
from Helper import Process

# Dictionary containing the words to look for, with an arbitrary weight (only for Ransoms and Ransomwares)
dict_ransom = {}

# Function looking for keywords related to a Ransom or Ransomware in a given Paste
def search_ransom(message):
	counter = 0
	str_DEBUG = ''
	paste = Paste.Paste(message)
	content = paste.get_p_content()
	for word in content.split():
		word = word.lower()
		#if a keyword is found, we add its weight to the total counter
		if word in dict_ransom:
			counter += dict_ransom[word]

			#for debugging! Delete ASAP
			str_DEBUG += (word+'\t')
	#for debugging! Delete ASAP
	print str_DEBUG
	#for debugging! Delete ASAP
	print counter

	# if the sum of threat indices is greater than 42, we consider that the Paste may be related to a Ransom or Ransomware
	if counter > 42 :

		#for debugging! Delete ASAP
		print str_DEBUG

		publisher.warning('{} may be a Ransom!'.format(paste.p_name))
	return None

# Module's main function

if __name__ == '__main__':
	# If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
	# Port of the redis instance used by pubsublogger
	publisher.port = 6380
	# Script is the default channel used for the modules.
	publisher.channel = 'Script'

	# Section name in bin/packages/modules.cfg
	config_section = 'Ransom'

	# Setup the I/O queues
	p = Process(config_section)

	# Sent to the logging a description of the module
	publisher.info("Run Ransom module")

	# Getting the dictionary from a file to the memory
	with open('nltk_data/corpora/dict/ransom.dic') as dict_file:
		for line in dict_file:
			k, v = line.split()
			dict_ransom[k] = int(v)

	# Endless loop getting messages from the input queue
	while True:
		# Get one message from the input queue
		message = p.get_from_set()
		if message is None:
			publisher.debug("{} queue is empty, waiting".format(config_section))
			time.sleep(1)
			continue

		# Do something with the message from the queue
		search_ransom(message)


#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
	Module for specific text analysis
	More global aim is to detect an attempt of: Ransom, Phishing, Social Engineering, etc.
	Here, only RANSOM is sought for now, and on every Paste.
"""

import time
import pprint
from packages import Paste
from packages import lib_refine
from pubsublogger import publisher
from Helper import Process

"""
	Forme du module :
	- analyser si ca contient du texte en langage naturel
	- Lower-Case les textes testes
	- ouvrir le fichier "dictionnaire", garder le contenu dans une variable dict["mot": poids] en memoire locale
	- analyser les mots significatifs
	- ignorer les repetitions (sinon, "database" augmenterait N fois le taux de menace, alors qu'il a un poids de seulement 1)
	- faire une somme des indices de "menaces"
	- ne lever une alerte qu'en cas de menace superieure a un seuil (arbitraire)
"""

# Dictionnaire contenant les mots a chercher (indicatifs de RANSOMWARE seulement)
dict_ransom = {}

# Fonction de recherche de mots-cles de rancons, encore peu optimisee
def search_ransom(message):
	counter = 0
	str_DEBUG = ''
	paste = Paste.Paste(message)
	content = paste.get_p_content()
	for word in content.split():
		word = word.lower()
		if word in dict_ransom:
			counter += dict_ransom[word]

			#for debugging! Delete ASAP
			str_DEBUG += (word+'\t')
			print counter
	print str_DEBUG
	print counter

	# if the list is greater than 4, we consider the Paste may contain a list of phone numbers
	if counter > 10 :
		# FOR DEBBUGGUNG ! DELETE ASAP !!
		print str_DEBUG
		publisher.warning('{} may be a Ransom!'.format(paste.p_name))
	return None

# fonction principale du module

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
	with open('nltk_data/corpora/dict/ransom.dic') as file:
		for line in file:
			k, v = line.split()
			dict_ransom[k] = v

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


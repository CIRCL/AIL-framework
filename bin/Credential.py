#!/usr/bin/env python2
# -*-coding:UTF-8 -*
import time
from packages import Paste
from pubsublogger import publisher 
from Helper import Process
import re

if __name__ == "__main__": 
	publisher.port = 6380 
	publisher.channel = "Script"
	config_section = "Credential"
	p = Process(config_section) 
	publisher.info("Find credentials")
		
	critical = 10

	regex_web = "/^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/"
	regex_cred = "[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}:[a-zA-Z0-9\_\-]+"
	while True:
		message = p.get_from_set() 
		if message is not None:	
			paste = Paste.Paste(message)
            		content = paste.get_p_content()
            		all_cred = re.findall(regex_cred, content)
            		if len(all_cred) > 0:
                		cred_set = set([])
				for cred in all_cred:
					cred_set.add(cred)

                		to_print = 'Cred;{};{};{};'.format(paste.p_source, paste.p_date, paste.p_name)
                		if len(cred_set) > 0:
                    			publisher.info(to_print)
					for cred in set(cred_set):
						print(cred)

					if len(cred_set) > critical:
						print("========> Found more than 10 credentials on this file : {}".format(message))
						site = re.findall(regex_web, content)
						publisher.warning(to_print)
						if len(site) > 0:
							print("=======> Probably on : {}".format(iter(site).next()))

		else:
            		publisher.debug("Script Credential is Idling 10s")
            		print 'Sleeping'
            		time.sleep(10)

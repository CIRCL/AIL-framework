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
	config_section = "Release"
	p = Process(config_section) 
	publisher.info("Release scripts to find release names")

	#REGEX :
	
	movie = "[a-zA-Z0-9.]+\.[0-9]{4}.[a-zA-Z0-9.]+\-[a-zA-Z]+"
	tv = "[a-zA-Z0-9.]+\.S[0-9]{2}E[0-9]{2}.[a-zA-Z0-9.]+\.[a-zA-Z0-9.]+\-[a-zA-Z0-9]+"
	xxx = "[a-zA-Z0-9._]+.XXX.[a-zA-Z0-9.]+\-[a-zA-Z0-9]+"
	
	regexs = [movie,tv,xxx]

	regex = re.compile('|'.join(regexs))
	while True:
		message = p.get_from_set() 
		if message is not None:		
			paste = Paste.Paste(message)
            		content = paste.get_p_content()
            		all_release = re.findall(regex, content)
            		if len(all_release) > 0:
                		release_set = set([])
				for rlz in all_release:
					release_set.add(rlz)

                		to_print = 'Release;{};{};{};'.format(paste.p_source, paste.p_date, paste.p_name)
                		if (len(release_set) > 0):
                    			publisher.warning('{}Checked {} valids'.format(to_print, len(release_set)))
					for rl in set(release_set):
        					#publisher.warning('{}'.format(rl))
						print(rl)
					if (len(release_set) > 10):
						print("----------------------------------- Found more than 10 releases on this file : {}".format(message))

                		else:
                    			publisher.info('{}Release related'.format(to_print))

				

		else:
            		publisher.debug("Script Release is Idling 10s")
            		print 'Sleeping'
            		time.sleep(10)

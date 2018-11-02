#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Regex Module
================

Search for regular expressions stored in a flat file + tag.
The flat file is automatically reloaded when the MTIME changed.

It uses the file 'packagess/regex.cfg'. Format:
Tag||Regex

Xavier Mertens <xavier@rootshell.be>

"""

import time
import os
import re
import signal
from pubsublogger import publisher

#from bin.packages import Paste
#from bin.Helper import Process

from packages import Paste
from Helper import Process

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

# Change the path to your preferred one
regexConfig = 'packages/regex.cfg'

regexes     = []

def load_regex(force = False):
    '''
    Load regexes from the config file and validate them
    If 'True' passed as argument, force to reload
    '''

    lregexes = regexes
    validate_regex = False

    try:
        stats = os.stat(regexConfig)
        mtime = int(stats.st_mtime)
        if mtime > time.time()-60 or force == True:
            # Regex config changed, reload the file
            print('Loading regular expressions')
            with open(regexConfig) as f:
                lines = f.readlines()
            lines = [x.strip() for x in lines] 
            validate_regex = True
    except:
        print('Cannot read {}'.format(regexConfig))
        return []

    if validate_regex:
        # Validate regexes read from the file
        line=1
        lregexes = []
        for l in lines:
            # Skip comments and empty lines
            if len(l) > 0:
                if l[0] == '#':
                    continue
                try:
                    re.compile(l.split('||')[1])
                except:  
                    print('Ignored line {}: Syntax error in "{}"'.format(line, regexConfig))
                    continue
                lregexes.append(l)
            line += 1
        print('DEBUG: regexes:')
        print(lregexes)
    return lregexes

def search_regex(paste):
    content = paste.get_p_content()
    find = False
    global regexes

    regexes = load_regex(False)

    for r in regexes:
        (tag,pattern) = r.split('||')

        signal.alarm(max_execution_time)
        try:
            if re.findall(pattern, content, re.MULTILINE|re.IGNORECASE):
                publisher.warning('Regex match: {} ({})'.format(pattern, tag))
                # Sanitize tag to make it easy to read
                tag = tag.strip().lower().replace(' ','-')
                print('regex {} found'.format(tag))
                msg = 'infoleak:automatic-detection="regex-{}";{}'.format(tag, message)
                p.populate_set_out(msg, 'Tags')
                find = True
        except TimeoutException:
            print ("{0} processing timeout".format(paste.p_path))
            continue
        else:
            signal.alarm(0)

    if find:
        #Send to duplicate
        p.populate_set_out(message, 'Duplicate')
        #send to Browse_warning_paste
        msg = ('regex;{}'.format(message))
        print(message)
        p.populate_set_out( msg, 'alertHandler')


if __name__ == '__main__':
    global regexes
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'Regex'

    # Setup the I/O queues
    p = Process(config_section)
    max_execution_time = p.config.getint(config_section, "max_execution_time")

    # Sent to the logging a description of the module
    publisher.info("Run Regex module ")

    # Load regular expressions from config file
    regexes = load_regex(True)

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        paste = Paste.Paste(message)
        search_regex(paste)

        # (Optional) Send that thing to the next queue

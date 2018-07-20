#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    DbDump


"""

import time

from pubsublogger import publisher

from Helper import Process
from packages import Paste

def get_lines(content):

    is_db_leak = False

    list_lines = content.splitlines()
    list_separators = []
    if len(list_lines) > 0:
        for line in list_lines:
            list_separators.append(search_separator(line))

    threshold_num_separator_line = 0
    # Minimum number of separator per line
    threshold_min_separator_line = 7
    same_separator = 0
    num_separator = 0
    current_separator = ''

    for separator in list_separators:
        if separator != '':
            #same separator on the next line
            if separator[0] == current_separator:
                if abs(separator[1] - num_separator) <= threshold_num_separator_line:
                    if num_separator > threshold_min_separator_line:
                        same_separator += 1
                    else:
                        num_separator = separator[1]
                        same_separator = 0
                else:
                    # FIXME: enhancement ?
                    num_separator = separator[1]

                if(same_separator >= 5):
                    is_db_leak = True
            #different operator
            else:
                #change the current separator
                current_separator = separator[0]
                same_separator = 0
                num_separator = 0

    return is_db_leak


def search_separator(line):
    list_separator = []
    #count separators
    #list_separator.append( (';', line.count(';')) )
    #list_separator.append( (',', line.count(',')) )
    list_separator.append( (';', line.count(';')) )
    list_separator.append( ('|', line.count('|')) )
    #list_separator.append( (':', line.count(':')) )

    separator = ''
    separator_number = 0

    # line separator
    for potential_separator in list_separator:
        if potential_separator[1] > separator_number:
                separator = potential_separator[0]
                separator_number = potential_separator[1]

    return (separator, separator_number)


if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    config_section = 'DbDump'

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("DbDump started")



    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        message = p.get_from_set()
        if message is None:

            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        filename = message
        paste = Paste.Paste(filename)

        # Do something with the message from the queue
        print(filename)
        content = paste.get_p_content()
        is_db_leak = get_lines(content)

        if is_db_leak:

            to_print = 'DbDump;{};{};{};'.format(
                paste.p_source, paste.p_date, paste.p_name)

            print('found DbDump')
            print(to_print)
            publisher.warning('{}Checked found Database Dump;{}'.format(
                    to_print, paste.p_path))

            msg = 'dbdump;{}'.format(filename)
            p.populate_set_out(msg, 'alertHandler')

            msg = 'dbdump;{}'.format(filename)
            p.populate_set_out(msg, 'Tags')

            #Send to duplicate
            p.populate_set_out(filename, 'Duplicate')

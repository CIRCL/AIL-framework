#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The ZMQ_PubSub_Categ Module
============================

This module is consuming the Redis-list created by the ZMQ_PubSub_Tokenize_Q
Module.

Each words files created under /files/ are representing categories.
This modules take these files and compare them to
the stream of data given by the ZMQ_PubSub_Tokenize_Q  Module.

When a word from a paste match one or more of these words file, the filename of
the paste is published/forwarded to the next modules.

Each category (each files) are representing a dynamic channel.
This mean that if you create 1000 files under /files/ you'll have 1000 channels
where every time there is a matching word to a category, the paste containing
this word will be pushed to this specific channel.

..note:: The channel will have the name of the file created.

Implementing modules can start here, create your own category file,
and then create your own module to treat the specific paste matching this
category.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances. (Redis)
*Categories files of words in /files/ need to be created
*Need the ZMQ_PubSub_Tokenize_Q Module running to be able to work properly.

"""

##################################
# Import External packages
##################################
import os
import argparse
import time
import re

##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from pubsublogger import publisher
from packages import Paste
from Helper import Process


class Categ(AbstractModule):
    """
    Categ module for AIL framework
    """

    def __init__(self):
        """
        Init Categ
        """
        super(Categ, self).__init__()

        self.matchingThreshold = self.process.config.getint("Categ", "matchingThreshold")

        # SCRIPT PARSER #
        parser = argparse.ArgumentParser(description='Start Categ module on files.')

        parser.add_argument(
            '-d', type=str, default="../files/",
            help='Path to the directory containing the category files.',
            action='store')

        args = parser.parse_args()

        self.redis_logger.info("Script Categ started")

        categories = ['CreditCards', 'Mail', 'Onion', 'Web', 'Credential', 'Cve', 'ApiKey']
        tmp_dict = {}
        for filename in categories:
            bname = os.path.basename(filename)
            tmp_dict[bname] = []
            with open(os.path.join(args.d, filename), 'r') as f:
                patterns = [r'%s' % ( re.escape(s.strip()) ) for s in f]
                tmp_dict[bname] = re.compile('|'.join(patterns), re.IGNORECASE)

        self.categ_items = tmp_dict.items()

        prec_filename = None


    def compute(self, message):
        # Cast message as paste
        paste = Paste.Paste(message)
        # Get paste content
        content = paste.get_p_content()

        # init categories found
        is_categ_found = False

        # Search for pattern categories in paste content
        for categ, pattern in self.categ_items:

            found = set(re.findall(pattern, content))
            lenfound = len(found)
            if lenfound >= self.matchingThreshold:
                is_categ_found = True
                msg = '{} {}'.format(paste.p_rel_path, lenfound)

                self.redis_logger.debug('%s;%s %s'%(self.module_name, msg, categ))
            
                # Export message to categ queue
                self.process.populate_set_out(msg, categ)

                self.redis_logger.info(
                    'Categ;{};{};{};Detected {} as {};{}'.format(
                        paste.p_source, paste.p_date, paste.p_name,
                        lenfound, categ, paste.p_rel_path))

        if not is_categ_found:
            self.redis_logger.debug('No %s found in this paste: %s'%(self.module_name, paste.p_name))


if __name__ == '__main__':
    
    module = Categ()
    module.run()

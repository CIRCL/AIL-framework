#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The ZMQ_PubSub_Categ Module
============================

Each words files created under /files/ are representing categories.
This modules take these files and compare them to
the content of an item.

When a word from a item match one or more of these words file, the filename of
the item / zhe item id is published/forwarded to the next modules.

Each category (each files) are representing a dynamic channel.
This mean that if you create 1000 files under /files/ you'll have 1000 channels
where every time there is a matching word to a category, the item containing
this word will be pushed to this specific channel.

..note:: The channel will have the name of the file created.

Implementing modules can start here, create your own category file,
and then create your own module to treat the specific paste matching this
category.

Requirements
------------

*Need running Redis instances. (Redis)
*Categories files of words in /files/ need to be created

"""

##################################
# Import External packages
##################################
import argparse
import os
import re
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Items import Item


class Categ(AbstractModule):
    """
    Categ module for AIL framework
    """

    def __init__(self, categ_files_dir=os.path.join(os.environ['AIL_HOME'], 'files')):
        """
        Init Categ
        """
        super(Categ, self).__init__()

        self.categ_files_dir = categ_files_dir

        # default = 1 string
        self.matchingThreshold = self.process.config.getint("Categ", "matchingThreshold")

        self.reload_categ_words()
        self.redis_logger.info("Script Categ started")

    # # TODO: trigger reload on change ( save last reload time, ...)
    def reload_categ_words(self):
        categories = ['CreditCards', 'Mail', 'Onion', 'Urls', 'Credential', 'Cve', 'ApiKey']
        tmp_dict = {}
        for filename in categories:
            bname = os.path.basename(filename)
            tmp_dict[bname] = []
            with open(os.path.join(self.categ_files_dir, filename), 'r') as f:
                patterns = [r'%s' % ( re.escape(s.strip()) ) for s in f]
                tmp_dict[bname] = re.compile('|'.join(patterns), re.IGNORECASE)
        self.categ_words = tmp_dict.items()

    def compute(self, message, r_result=False):
        # Create Item Object
        item = Item(message)
        # Get item content
        content = item.get_content()
        categ_found = []

        # Search for pattern categories in item content
        for categ, pattern in self.categ_words:

            found = set(re.findall(pattern, content))
            lenfound = len(found)
            if lenfound >= self.matchingThreshold:
                categ_found.append(categ)
                msg = f'{item.get_id()} {lenfound}'

                # Export message to categ queue
                print(msg, categ)
                self.send_message_to_queue(msg, categ)

                self.redis_logger.info(
                    f'Categ;{item.get_source()};{item.get_date()};{item.get_basename()};Detected {lenfound} as {categ};{item.get_id()}')
        if r_result:
            return categ_found

        # DIRTY FIX AIL SYNC
        # # FIXME:  DIRTY FIX
        message = f'{item.get_type()};{item.get_subtype(r_str=True)};{item.get_id()}'
        print(message)
        self.send_message_to_queue(message, 'SyncModule')


if __name__ == '__main__':

    # SCRIPT PARSER #
    parser = argparse.ArgumentParser(description='Start Categ module on files.')
    parser.add_argument(
        '-d', type=str, default=os.path.join(os.environ['AIL_HOME'], 'files'),
        help='Path to the directory containing the category files.',
        action='store')
    args = parser.parse_args()

    module = Categ(categ_files_dir=args.d)
    module.run()

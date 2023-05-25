#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import logging.config
import sys
import time

from requests.exceptions import ConnectionError

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib import ail_logger
from lib import crawlers
from lib.ConfigLoader import ConfigLoader
from lib.objects.Domains import Domain
from lib.objects.Items import Item
from lib.objects import Screenshots
from lib.objects import Titles

logging.config.dictConfig(ail_logger.get_config(name='crawlers'))

class Crawler(AbstractModule):

    def __init__(self):
        super(Crawler, self, ).__init__()

        self.logger = logging.getLogger(f'{self.__class__.__name__}')

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        config_loader = ConfigLoader()

        self.default_har = config_loader.get_config_boolean('Crawler', 'default_har')
        self.default_screenshot = config_loader.get_config_boolean('Crawler', 'default_screenshot')
        self.default_depth_limit = config_loader.get_config_int('Crawler', 'default_depth_limit')

        # TODO: LIMIT MAX NUMBERS OF CRAWLED PAGES

        # update hardcoded blacklist
        crawlers.load_blacklist()
        # update captures cache
        crawlers.reload_crawler_captures()

        self.crawler_scheduler = crawlers.CrawlerScheduler()

        # LACUS
        self.lacus = crawlers.get_lacus()
        self.is_lacus_up = crawlers.is_lacus_connected(delta_check=0)

        # Capture
        self.har = None
        self.screenshot = None
        self.root_item = None
        self.har_dir = None
        self.items_dir = None
        self.domain = None

        # TODO Replace with warning list ???
        self.placeholder_screenshots = {'27e14ace10b0f96acd2bd919aaa98a964597532c35b6409dff6cc8eec8214748'}

        # Send module state to logs
        self.logger.info('Crawler initialized')

    def refresh_lacus_status(self):
        try:
            lacus_up = self.is_lacus_up
            self.is_lacus_up = crawlers.get_lacus().is_up
            # refresh lacus
            if not lacus_up and self.is_lacus_up:
                self.lacus = crawlers.get_lacus()
        except:
            self.is_lacus_up = False
        if not self.is_lacus_up:
            print("Can't reach lacus server", int(time.time()))
            time.sleep(30)

    def print_crawler_start_info(self, url, domain_url):
        print()
        print()
        print('\033[92m------------------START CRAWLER------------------\033[0m')
        print(f'crawler type:     {self.domain}')
        print('\033[92m-------------------------------------------------\033[0m')
        print(f'url:         {url}')
        print(f'domain:      {self.domain}')
        print(f'domain_url:  {domain_url}')
        print()

    def get_message(self):
        # Crawler Scheduler
        self.crawler_scheduler.update_queue()
        self.crawler_scheduler.process_queue()

        self.refresh_lacus_status() # TODO LOG ERROR
        if not self.is_lacus_up:
            return None

        # Check if a new Capture can be Launched
        if crawlers.get_nb_crawler_captures() < crawlers.get_crawler_max_captures():
            task_row = crawlers.add_task_to_lacus_queue()
            if task_row:
                task_uuid, priority = task_row
                try:
                    self.enqueue_capture(task_uuid, priority)
                except ConnectionError:
                    print(task_row)
                    task = crawlers.CrawlerTask(task_uuid)
                    task.add_to_db_crawler_queue(priority)
                    self.refresh_lacus_status()
                    return None

        # Get CrawlerCapture Object
        capture = crawlers.get_crawler_capture()
        if capture:
            try:
                status = self.lacus.get_capture_status(capture.uuid)
                if status != crawlers.CaptureStatus.DONE:  # TODO ADD GLOBAL TIMEOUT-> Save start time ### print start time
                    capture.update(status)
                    print(capture.uuid, crawlers.CaptureStatus(status).name, int(time.time()))
                else:
                    return capture

            except ConnectionError:
                print(capture.uuid)
                capture.update(self, -1)
                self.refresh_lacus_status()

        time.sleep(self.pending_seconds)

    def enqueue_capture(self, task_uuid, priority):
        task = crawlers.CrawlerTask(task_uuid)
        # print(task)
        # task = {
        #         'uuid': task_uuid,
        #         'url': 'https://foo.be',
        #         'domain': 'foo.be',
        #         'depth': 1,
        #         'har': True,
        #         'screenshot': True,
        #         'user_agent': crawlers.get_default_user_agent(),
        #         'cookiejar': [],
        #         'header': '',
        #         'proxy': 'force_tor',
        #         'parent': 'manual',
        # }

        url = task.get_url()
        force = priority != 0
        # TODO timeout

        # TODO HEADER
        # capture_uuid = self.lacus.enqueue(url='https://cpg.circl.lu:7000',
        #                                   force=force,
        #                                   general_timeout_in_sec=120)

        capture_uuid = self.lacus.enqueue(url=url,
                                          depth=task.get_depth(),
                                          user_agent=task.get_user_agent(),
                                          proxy=task.get_proxy(),
                                          cookies=task.get_cookies(),
                                          force=force,
                                          general_timeout_in_sec=90)  # TODO increase timeout if onion ????

        crawlers.create_capture(capture_uuid, task_uuid)
        print(task.uuid, capture_uuid, 'launched')
        return capture_uuid

    # CRAWL DOMAIN
    def compute(self, capture):
        print('saving capture', capture.uuid)

        task = capture.get_task()
        domain = task.get_domain()
        print(domain)

        self.domain = Domain(domain)

        epoch = int(time.time())
        parent_id = task.get_parent()

        entries = self.lacus.get_capture(capture.uuid)
        print(entries['status'])
        self.har = task.get_har()
        self.screenshot = task.get_screenshot()
        # DEBUG
        # self.har = True
        # self.screenshot = True
        str_date = crawlers.get_current_date(separator=True)
        self.har_dir = crawlers.get_date_har_dir(str_date)
        self.items_dir = crawlers.get_date_crawled_items_source(str_date)
        self.root_item = None

        # Save Capture
        self.save_capture_response(parent_id, entries)

        self.domain.update_daterange(str_date.replace('/', ''))
        # Origin + History
        if self.root_item:
            self.domain.set_last_origin(parent_id)
            self.domain.add_history(epoch, root_item=self.root_item)
        elif self.domain.was_up():
            self.domain.add_history(epoch, root_item=epoch)

        crawlers.update_last_crawled_domain(self.domain.get_domain_type(), self.domain.id, epoch)
        print('capture:', capture.uuid, 'completed')
        print('task:   ', task.uuid, 'completed')
        print()
        task.remove()

    def save_capture_response(self, parent_id, entries):
        print(entries.keys())
        if 'error' in entries:
            # TODO IMPROVE ERROR MESSAGE
            self.logger.warning(str(entries['error']))
            print(entries['error'])
            if entries.get('html'):
                print('retrieved content')
                # print(entries.get('html'))

        if 'last_redirected_url' in entries and entries['last_redirected_url']:
            last_url = entries['last_redirected_url']
            unpacked_last_url = crawlers.unpack_url(last_url)
            current_domain = unpacked_last_url['domain']
            # REDIRECTION TODO CHECK IF TYPE CHANGE
            if current_domain != self.domain.id and not self.root_item:
                self.logger.warning(f'External redirection {self.domain.id} -> {current_domain}')
                print(f'External redirection {self.domain.id} -> {current_domain}')
                if not self.root_item:
                    self.domain = Domain(current_domain)
        # TODO LAST URL
        # FIXME
        else:
            last_url = f'http://{self.domain.id}'

        if 'html' in entries and entries['html']:
            item_id = crawlers.create_item_id(self.items_dir, self.domain.id)
            print(item_id)
            gzip64encoded = crawlers.get_gzipped_b64_item(item_id, entries['html'])
            # send item to Global
            relay_message = f'crawler {item_id} {gzip64encoded}'
            self.add_message_to_queue(relay_message, 'Importers')

            # Tag
            msg = f'infoleak:submission="crawler";{item_id}'
            self.add_message_to_queue(msg, 'Tags')

            crawlers.create_item_metadata(item_id, last_url, parent_id)
            if self.root_item is None:
                self.root_item = item_id
            parent_id = item_id

            item = Item(item_id)

            title_content = crawlers.extract_title_from_html(entries['html'])
            if title_content:
                title = Titles.create_title(title_content)
                title.add(item.get_date(), item_id)

            # SCREENSHOT
            if self.screenshot:
                if 'png' in entries and entries['png']:
                    screenshot = Screenshots.create_screenshot(entries['png'], b64=False)
                    if screenshot:
                        if not screenshot.is_tags_safe():
                            unsafe_tag = 'dark-web:topic="pornography-child-exploitation"'
                            self.domain.add_tag(unsafe_tag)
                            item.add_tag(unsafe_tag)
                        # Remove Placeholder pages # TODO Replace with warning list ???
                        if screenshot.id not in self.placeholder_screenshots:
                            # Create Correlations
                            screenshot.add_correlation('item', '', item_id)
                            screenshot.add_correlation('domain', '', self.domain.id)
            # HAR
            if self.har:
                if 'har' in entries and entries['har']:
                    crawlers.save_har(self.har_dir, item_id, entries['har'])
        # Next Children
        entries_children = entries.get('children')
        if entries_children:
            for children in entries_children:
                self.save_capture_response(parent_id, children)


if __name__ == '__main__':
    module = Crawler()
    module.debug = True
    module.run()

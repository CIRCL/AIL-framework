#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import logging.config
import sys
import time

from pyail import PyAIL
from requests.exceptions import ConnectionError

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib import ail_logger
from lib import crawlers
from lib.ConfigLoader import ConfigLoader
from lib.exceptions import TimeoutException, OnionFilteringError
from lib.Tag import get_domain_vanity_tags
from lib.objects import CookiesNames
from lib.objects import Etags
from lib.objects.Domains import Domain
from lib.objects import DomHashs
from lib.objects import Favicons
from lib.objects.Items import Item
from lib.objects import Screenshots
from lib.objects import Titles
from trackers.Tracker_Yara import Tracker_Yara

logging.config.dictConfig(ail_logger.get_config(name='crawlers'))

# SIGNAL ALARM
import signal
def timeout_handler(signum, frame):
    raise TimeoutException


signal.signal(signal.SIGALRM, timeout_handler)


class Crawler(AbstractModule):

    def __init__(self):
        super(Crawler, self, ).__init__()

        self.logger = logging.getLogger(f'{self.__class__.__name__}')

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        self.tracker_yara = Tracker_Yara(queue=False)

        self.vanity_tags = get_domain_vanity_tags()
        print('vanity tags:', self.vanity_tags)

        config_loader = ConfigLoader()

        self.filter_unsafe_onion = crawlers.is_onion_filter_enabled(cache=False)
        self.filter_unknown_onion = crawlers.is_onion_filter_unknown(cache=False)
        self.last_config_check = int(time.time())

        self.default_har = config_loader.get_config_boolean('Crawler', 'default_har')
        self.default_screenshot = config_loader.get_config_boolean('Crawler', 'default_screenshot')
        self.default_depth_limit = config_loader.get_config_int('Crawler', 'default_depth_limit')

        ail_url_to_push_discovery = config_loader.get_config_str('Crawler', 'ail_url_to_push_onion_discovery')
        ail_key_to_push_discovery = config_loader.get_config_str('Crawler', 'ail_key_to_push_onion_discovery')
        if ail_url_to_push_discovery and ail_key_to_push_discovery:
            ail = PyAIL(ail_url_to_push_discovery, ail_key_to_push_discovery, ssl=False)
            if ail.ping_ail():
                self.ail_to_push_discovery = ail
        else:
            self.ail_to_push_discovery = None

        # TODO: LIMIT MAX NUMBERS OF CRAWLED PAGES

        # update hardcoded blacklist
        crawlers.load_blacklist()
        # update captures cache
        crawlers.reload_crawler_captures()
        # update crawler queue stats
        crawlers.reload_crawlers_stats()

        self.crawler_scheduler = crawlers.CrawlerScheduler()

        # LACUS
        self.lacus = crawlers.get_lacus()
        self.is_lacus_up = crawlers.is_lacus_connected(delta_check=0)

        # Capture
        self.har = None
        self.screenshot = None
        self.root_item = None
        self.date = None
        self.items_dir = None
        self.original_domain = None
        self.domain = None
        self.parent = None

        # TODO Replace with warning list ???
        self.placeholder_screenshots = {'07244254f73e822bd4a95d916d8b27f2246b02c428adc29082d09550c6ed6e1a'   # blank
                                        '27e14ace10b0f96acd2bd919aaa98a964597532c35b6409dff6cc8eec8214748',  # not found
                                        '3e66bf4cc250a68c10f8a30643d73e50e68bf1d4a38d4adc5bfc4659ca2974c0'}  # 404

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
            try:
                time.sleep(30)
            except TimeoutException:
                pass

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

        self.refresh_lacus_status()  # TODO LOG ERROR
        if not self.is_lacus_up:
            return None

        # Refresh Config
        if int(time.time()) - self.last_config_check > 60:
            self.filter_unsafe_onion = crawlers.is_onion_filter_enabled()
            self.filter_unknown_onion = crawlers.is_onion_filter_unknown()
            self.last_config_check = int(time.time())

        # Check if a new Capture can be Launched
        if crawlers.get_nb_crawler_captures() < crawlers.get_crawler_max_captures():
            task_row = crawlers.add_task_to_lacus_queue()
            if task_row:
                task, priority = task_row
                domain = task.get_domain()
                if self.filter_unsafe_onion:
                    if domain.endswith('.onion'):
                        try:
                            if not crawlers.check_if_onion_is_safe(domain, unknown=self.filter_unknown_onion):
                                # print('---------------------------------------------------------')
                                # print('DOMAIN FILTERED')
                                task.delete()
                                return None
                        except OnionFilteringError:
                            task.reset()
                            self.logger.warning(f'Onion Filtering Connection Error, {task.uuid} Send back in queue')
                            time.sleep(10)
                            return None

                task.start()
                task_uuid = task.uuid
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
                print(status)
                if status == crawlers.CaptureStatus.DONE:
                    return capture
                elif status == crawlers.CaptureStatus.UNKNOWN:
                    capture_start = capture.get_start_time(r_str=False)
                    if capture_start == 0:
                        task = capture.get_task()
                        task.delete()
                        capture.delete()
                        self.logger.warning(f'capture UNKNOWN ERROR STATE, {task.uuid} Removed from queue')
                        return None
                    if int(time.time()) - capture_start > 600:  # TODO ADD in new crawler config
                        task = capture.get_task()
                        task.reset()
                        capture.delete()
                        self.logger.warning(f'capture UNKNOWN Timeout, {task.uuid} Send back in queue')
                    else:
                        capture.update(status)
                elif status == crawlers.CaptureStatus.QUEUED:
                    capture_start = capture.get_start_time(r_str=False)
                    if int(time.time()) - capture_start > 36000:  # TODO ADD in new crawler config
                        task = capture.get_task()
                        task.reset()
                        capture.delete()
                        self.logger.warning(f'capture QUEUED Timeout, {task.uuid}, {task.get_url()} Send back in queue, start_time={capture_start}')
                    else:
                        capture.update(status)
                    print(capture.uuid, crawlers.CaptureStatus(status).name, int(time.time()))
                elif status == crawlers.CaptureStatus.ONGOING:
                    capture.update(status)
                    print(capture.uuid, crawlers.CaptureStatus(status).name, int(time.time()))
                # Invalid State
                else:
                    task = capture.get_task()
                    task.reset()
                    capture.delete()
                    self.logger.warning(f'ERROR INVALID CAPTURE STATUS {status}, {task.uuid} Send back in queue')

            except ConnectionError:
                self.logger.warning(f'Lacus ConnectionError, capture {capture.uuid}')
                capture.update(-1)
                self.refresh_lacus_status()

        try:
            time.sleep(self.pending_seconds)
        except TimeoutException:
            pass

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

        # with_favicon = True,
        capture_uuid = self.lacus.enqueue(url=url,
                                          depth=task.get_depth(),
                                          user_agent=task.get_user_agent(),
                                          proxy=task.get_proxy(),
                                          cookies=task.get_cookies(),
                                          with_favicon=True,
                                          force=force,
                                          general_timeout_in_sec=90)  # TODO increase timeout if onion ????

        crawlers.create_capture(capture_uuid, task_uuid)
        print(task.uuid, capture_uuid, 'launched')

        if self.ail_to_push_discovery:

            if task.get_depth() == 1 and priority < 10 and task.get_domain().endswith('.onion'):
                har = task.get_har()
                screenshot = task.get_screenshot()
                # parent_id = task.get_parent()
                # if parent_id != 'manual' and parent_id != 'auto':
                #     parent = parent_id[19:-36]
                # else:
                #     parent = 'AIL_capture'

                if not url:
                    raise Exception(f'Error: url is None, {task.uuid}, {capture_uuid}, {url}')

                self.ail_to_push_discovery.add_crawler_capture(task_uuid, capture_uuid, url, har=har,  # parent=parent,
                                                               screenshot=screenshot, depth_limit=1, proxy='force_tor')
                print(task.uuid, capture_uuid, url, 'Added to ail_to_push_discovery')
        return capture_uuid

    # CRAWL DOMAIN
    def compute(self, capture):
        print('saving capture', capture.uuid)

        task = capture.get_task()
        domain = task.get_domain()
        print(domain)
        if not domain:
            if self.debug:
                raise Exception(f'Error: domain {domain} - task {task.uuid} - capture {capture.uuid}')
            else:
                self.logger.critical(f'Error: domain {domain} - task {task.uuid} - capture {capture.uuid}')
                print(f'Error: domain {domain}')
            return None

        self.domain = Domain(domain)
        self.parent = self.domain.get_parent()
        self.original_domain = Domain(domain)

        epoch = int(time.time())
        parent_id = task.get_parent()

        entries = self.lacus.get_capture(capture.uuid)

        print(entries.get('status'))
        self.har = task.get_har()
        self.screenshot = task.get_screenshot()
        # DEBUG
        # self.har = True
        # self.screenshot = True
        self.date = crawlers.get_current_date(separator=True)
        self.items_dir = crawlers.get_date_crawled_items_source(self.date)
        self.root_item = None

        # Save Capture
        saved = self.save_capture_response(parent_id, entries)
        if saved:
            if self.parent != 'lookup':
                # Update domain first/last seen
                self.domain.update_daterange(self.date.replace('/', ''))
            # Origin + History + tags
            if self.root_item:
                self.domain.set_last_origin(parent_id)
                # Vanity
                self.domain.update_vanity_cluster()
                domain_vanity = self.domain.get_vanity()
                if domain_vanity in self.vanity_tags:
                    for tag in self.vanity_tags[domain_vanity]:
                        self.domain.add_tag(tag)
                # Tags
                for tag in task.get_tags():
                    self.domain.add_tag(tag)
            # Crawler stats
            self.domain.add_history(epoch, root_item=self.root_item)

            if self.domain != self.original_domain:  # TODO ADD RELATIONSHIP REDIRECT
                self.original_domain.update_daterange(self.date.replace('/', ''))
                if self.root_item:
                    self.original_domain.set_last_origin(parent_id)
                    # Tags
                    for tag in task.get_tags():
                        self.domain.add_tag(tag)
                self.original_domain.add_history(epoch, root_item=self.root_item)
                # crawlers.update_last_crawled_domain(self.original_domain.get_domain_type(), self.original_domain.id, epoch)

            crawlers.update_last_crawled_domain(self.domain.get_domain_type(), self.domain.id, epoch)
            print('capture:', capture.uuid, 'completed')
            print('task:   ', task.uuid, 'completed')
            print()
        else:
            print('capture:', capture.uuid, 'Unsafe Content Filtered')
            print('task:   ', task.uuid, 'Unsafe Content Filtered')
            print()

        # onion messages correlation
        if crawlers.is_domain_correlation_cache(self.original_domain.id):
            crawlers.save_domain_correlation_cache(self.original_domain.was_up(), domain)

        task.remove()
        self.root_item = None

    def save_capture_response(self, parent_id, entries):
        print(entries.keys())
        if 'error' in entries:
            # TODO IMPROVE ERROR MESSAGE
            self.logger.warning(str(entries['error']))
            print(entries.get('error'))
            if entries.get('html'):
                print('retrieved content')
                # print(entries.get('html'))

        if 'last_redirected_url' in entries and entries.get('last_redirected_url'): # TODO ADD RELATIONSHIP REDIRECT
            last_url = entries['last_redirected_url']
            unpacked_last_url = crawlers.unpack_url(last_url)
            current_domain = unpacked_last_url['domain']
            # REDIRECTION TODO CHECK IF TYPE CHANGE
            if current_domain != self.domain.id and not self.root_item:
                self.logger.warning(f'External redirection {self.domain.id} -> {current_domain}')
                if not self.root_item:
                    self.domain = Domain(current_domain)
                    # Filter Domain
                    if self.filter_unsafe_onion:
                        if current_domain.endswith('.onion'):
                            if not crawlers.check_if_onion_is_safe(current_domain, unknown=self.filter_unknown_onion):
                                return False

        # TODO LAST URL
        # FIXME
        else:
            last_url = f'http://{self.domain.id}'

        if 'html' in entries and entries.get('html'):
            item_id = crawlers.create_item_id(self.items_dir, self.domain.id)
            item = Item(item_id)
            print(item.id)

            gzip64encoded = crawlers.get_gzipped_b64_item(item.id, entries['html'])
            # send item to Global
            relay_message = f'crawler {gzip64encoded}'
            self.add_message_to_queue(obj=item, message=relay_message, queue='Importers')

            # Tag # TODO replace me with metadata to tags
            msg = f'infoleak:submission="crawler"'  # TODO FIXME
            self.add_message_to_queue(obj=item, message=msg, queue='Tags')

            # TODO replace me with metadata to add
            crawlers.create_item_metadata(item_id, last_url, parent_id)
            if self.root_item is None:
                self.root_item = item_id
            parent_id = item_id

            # DOM-HASH
            dom_hash = DomHashs.create(entries['html'])
            dom_hash.add(self.date.replace('/', ''), item)
            dom_hash.add_correlation('domain', '', self.domain.id)

            # TITLE
            signal.alarm(60)
            try:
                title_content = crawlers.extract_title_from_html(entries['html'])
            except TimeoutException:
                self.logger.warning(f'BeautifulSoup HTML parser timeout: {item_id}')
                title_content = None
            else:
                signal.alarm(0)

            if title_content:
                title = Titles.create_title(title_content)
                title.add(item.get_date(), item)
                # Tracker
                self.tracker_yara.compute_manual(title)
                # if not title.is_tags_safe():
                #     unsafe_tag = 'dark-web:topic="pornography-child-exploitation"'
                #     self.domain.add_tag(unsafe_tag)
                #     item.add_tag(unsafe_tag)
                self.add_message_to_queue(obj=title, message=msg, queue='Titles')

            # SCREENSHOT
            if self.screenshot:
                if 'png' in entries and entries.get('png'):
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
                        self.add_message_to_queue(obj=screenshot, queue='Images')
            # HAR
            if self.har:
                if 'har' in entries and entries.get('har'):
                    har_id = crawlers.create_har_id(self.date, item_id)
                    crawlers.save_har(har_id, entries['har'])
                    for cookie_name in crawlers.extract_cookies_names_from_har(entries['har']):
                        print(cookie_name)
                        cookie = CookiesNames.create(cookie_name)
                        cookie.add(self.date.replace('/', ''), self.domain)
                    for etag_content in crawlers.extract_etag_from_har(entries['har']):
                        print(etag_content)
                        etag = Etags.create(etag_content)
                        etag.add(self.date.replace('/', ''), self.domain)
                    crawlers.extract_hhhash(entries['har'], self.domain.id, self.date.replace('/', ''))

            # FAVICON
            if entries.get('potential_favicons'):
                for favicon in entries['potential_favicons']:
                    fav = Favicons.create(favicon)
                    fav.add(item.get_date(), item)

        # Next Children
        entries_children = entries.get('children')
        if entries_children:
            for children in entries_children:
                self.save_capture_response(parent_id, children)
        return True


if __name__ == '__main__':
    module = Crawler()
    module.debug = True
    module.run()

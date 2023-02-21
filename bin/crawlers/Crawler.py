#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib import crawlers
from lib.ConfigLoader import ConfigLoader
from lib.objects.Domains import Domain
from lib.objects import Screenshots

class Crawler(AbstractModule):

    def __init__(self):
        super(Crawler, self, ).__init__(logger_channel='Crawler')

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        config_loader = ConfigLoader()
        self.r_log_submit = config_loader.get_redis_conn('Redis_Log_submit')

        self.default_har = config_loader.get_config_boolean('Crawler', 'default_har')
        self.default_screenshot = config_loader.get_config_boolean('Crawler', 'default_screenshot')
        self.default_depth_limit = config_loader.get_config_int('Crawler', 'default_depth_limit')

        # TODO: LIMIT MAX NUMBERS OF CRAWLED PAGES

        # update hardcoded blacklist
        crawlers.load_blacklist()
        # update captures cache
        crawlers.reload_crawler_captures()

        # LACUS
        self.lacus = crawlers.get_lacus()

        # Capture
        self.har = None
        self.screenshot = None
        self.root_item = None
        self.har_dir = None
        self.items_dir = None
        self.domain = None

        # Send module state to logs
        self.redis_logger.info('Crawler initialized')

    def print_crawler_start_info(self, url, domain, domain_url):
        print()
        print()
        print('\033[92m------------------START CRAWLER------------------\033[0m')
        print(f'crawler type:     {domain}')
        print('\033[92m-------------------------------------------------\033[0m')
        print(f'url:         {url}')
        print(f'domain:      {domain}')
        print(f'domain_url:  {domain_url}')
        print()

    def get_message(self):
        # Check if a new Capture can be Launched
        if crawlers.get_nb_crawler_captures() < crawlers.get_crawler_max_captures():
            task_row = crawlers.add_task_to_lacus_queue()
            if task_row:
                print(task_row)
                task_uuid, priority = task_row
                self.enqueue_capture(task_uuid, priority)

        # Get CrawlerCapture Object
        capture = crawlers.get_crawler_capture()
        if capture:
            print(capture.uuid)
            status = self.lacus.get_capture_status(capture.uuid)
            if status != crawlers.CaptureStatus.DONE:  # TODO ADD GLOBAL TIMEOUT-> Save start time
                capture.update(status)
                print(capture.uuid, status, int(time.time()))
            else:
                self.compute(capture)
                capture.delete() # TODO DELETE TASK ONLY IF NOT SCHEDULED TASKS
                print('capture', capture.uuid, 'completed')

        time.sleep(self.pending_seconds)

    def enqueue_capture(self, task_uuid, priority):
        task = crawlers.CrawlerTask(task_uuid)
        print(task)
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

        capture_uuid = self.lacus.enqueue(url=url,
                                          depth=task.get_depth(),
                                          user_agent=task.get_user_agent(),
                                          proxy=task.get_proxy(),
                                          cookies=task.get_cookies(),
                                          force=force,
                                          general_timeout_in_sec=90)

        crawlers.create_capture(capture_uuid, task_uuid)
        print(task.uuid, capture_uuid, 'launched')
        return capture_uuid

    # CRAWL DOMAIN
    # TODO: CATCH ERRORS
    def compute(self, capture):
        print('saving capture', capture.uuid)

        task = capture.get_task()
        domain = task.get_domain()
        print(domain)

        self.domain = Domain(domain)

        # TODO CHANGE EPOCH
        epoch = int(time.time())
        parent_id = task.get_parent()

        entries = self.lacus.get_capture(capture.uuid)
        print(entries['status'])
        self.har = task.get_har()
        self.screenshot = task.get_screenshot()
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
        task.clear()

    def save_capture_response(self, parent_id, entries):
        print(entries.keys())
        if 'error' in entries:
            # TODO IMPROVE ERROR MESSAGE
            self.redis_logger.warning(str(entries['error']))
            print(entries['error'])
            if entries.get('html'):
                print('retrieved content')
                # print(entries.get('html'))

        # TODO LOGS IF != domain
        if 'last_redirected_url' in entries and entries['last_redirected_url']:
            last_url = entries['last_redirected_url']
            unpacked_last_url = crawlers.unpack_url(last_url)
            current_domain = unpacked_last_url['domain']
            # REDIRECTION TODO CHECK IF WEB
            if current_domain != self.domain.id and not self.root_item:
                self.redis_logger.warning(f'External redirection {self.domain.id} -> {current_domain}')
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
            relay_message = f'{item_id} {gzip64encoded}'
            self.send_message_to_queue(relay_message, 'Mixer')
            # increase nb of paste by feeder name
            self.r_log_submit.hincrby('mixer_cache:list_feeder', 'crawler', 1)

            # Tag
            msg = f'infoleak:submission="crawler";{item_id}'
            self.send_message_to_queue(msg, 'Tags')

            crawlers.create_item_metadata(item_id, last_url, parent_id)
            if self.root_item is None:
                self.root_item = item_id
            parent_id = item_id

            # SCREENSHOT
            if self.screenshot:
                if 'png' in entries and entries['png']:
                    screenshot = Screenshots.create_screenshot(entries['png'], b64=False)
                    if screenshot:
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
    # module.compute(('ooooo', 0))
    module.run()


##################################
##################################
##################################
##################################
##################################

# def update_auto_crawler():
#     current_epoch = int(time.time())
#     list_to_crawl = redis_crawler.zrangebyscore('crawler_auto_queue', '-inf', current_epoch)
#     for elem_to_crawl in list_to_crawl:
#         mess, type = elem_to_crawl.rsplit(';', 1)
#         redis_crawler.sadd('{}_crawler_priority_queue'.format(type), mess)
#         redis_crawler.zrem('crawler_auto_queue', elem_to_crawl)

# Extract info form url (url, domain, domain url, ...)
# def unpack_url(url):
#     to_crawl = {}
#     faup.decode(url)
#     url_unpack = faup.get()
#     to_crawl['domain'] = to_crawl['domain'].lower()
#     new_url_host = url_host.lower()
#     url_lower_case = url.replace(url_host, new_url_host, 1)
#
#     if url_unpack['scheme'] is None:
#         to_crawl['scheme'] = 'http'
#         url= 'http://{}'.format(url_lower_case)
#     else:
#         try:
#             scheme = url_unpack['scheme'].decode()
#         except Exception as e:
#             scheme = url_unpack['scheme']
#         if scheme in default_proto_map:
#             to_crawl['scheme'] = scheme
#             url = url_lower_case
#         else:
#             redis_crawler.sadd('new_proto', '{} {}'.format(scheme, url_lower_case))
#             to_crawl['scheme'] = 'http'
#             url= 'http://{}'.format(url_lower_case.replace(scheme, '', 1))
#
#     if url_unpack['port'] is None:
#         to_crawl['port'] = default_proto_map[to_crawl['scheme']]
#     else:
#         try:
#             port = url_unpack['port'].decode()
#         except:
#             port = url_unpack['port']
#         # Verify port number                        #################### make function to verify/correct port number
#         try:
#             int(port)
#         # Invalid port Number
#         except Exception as e:
#             port = default_proto_map[to_crawl['scheme']]
#         to_crawl['port'] = port
#
#     #if url_unpack['query_string'] is None:
#     #    if to_crawl['port'] == 80:
#     #        to_crawl['url']= '{}://{}'.format(to_crawl['scheme'], url_unpack['host'].decode())
#     #    else:
#     #        to_crawl['url']= '{}://{}:{}'.format(to_crawl['scheme'], url_unpack['host'].decode(), to_crawl['port'])
#     #else:
#     #    to_crawl['url']= '{}://{}:{}{}'.format(to_crawl['scheme'], url_unpack['host'].decode(), to_crawl['port'], url_unpack['query_string'].decode())
#
#     to_crawl['url'] = url
#     if to_crawl['port'] == 80:
#         to_crawl['domain_url'] = '{}://{}'.format(to_crawl['scheme'], new_url_host)
#     else:
#         to_crawl['domain_url'] = '{}://{}:{}'.format(to_crawl['scheme'], new_url_host, to_crawl['port'])
#
#     try:
#         to_crawl['tld'] = url_unpack['tld'].decode()
#     except:
#         to_crawl['tld'] = url_unpack['tld']
#
#     return to_crawl

# ##################################################### add ftp ???
        # update_auto_crawler()

                # # add next auto Crawling in queue:
                # if to_crawl['paste'] == 'auto':
                #     redis_crawler.zadd('crawler_auto_queue', int(time.time()+crawler_config['crawler_options']['time']) , '{};{}'.format(to_crawl['original_message'], to_crawl['type_service']))
                #     # update list, last auto crawled domains
                #     redis_crawler.lpush('last_auto_crawled', '{}:{};{}'.format(url_data['domain'], url_data['port'], date['epoch']))
                #     redis_crawler.ltrim('last_auto_crawled', 0, 9)
                #

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send an URL to the crawler - Create a crawler task
================

Import URL to be crawled by AIL and then analysed

"""

import argparse
import os
from pyail import PyAIL
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

def check_frequency(value):
    value = int(value)
    if value <= 0:
        raise argparse.ArgumentTypeError(f'Error: Invalid frequency {value}')


if __name__ == "__main__":

    # TODO add c argument for config file
    parser = argparse.ArgumentParser(description='Send an URL to the crawler - Create a crawler task')
    parser.add_argument('-u', '--url', type=str, help='URL to crawl', required=True)
    parser.add_argument('-k', '--key', type=str, help='AIL API Key', required=True)
    parser.add_argument('-a', '--ail', type=str, help='AIL URL')
    parser.add_argument('-d', '--depth', type=int, default=1, help='Depth limit')  # TODO improve me
    parser.add_argument('--cookiejar', type=str, help='Cookiejar uuid')
    parser.add_argument('-p', '--proxy', type=str, help='Proxy address to use, "web" and "tor" can be used as shortcut (web is used by default if the domain isn\'t an onion)')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--har', dest='har', action='store_true', help='Save HAR')
    group.add_argument('--no-har', dest='har', action='store_false', help='Don\'t save HAR')
    parser.set_defaults(har=None)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--screenshot', dest='screenshot', action='store_true', help='Save screenshot')
    group.add_argument('--no-screenshot', dest='screenshot', action='store_false', help='Don\'t save screenshot')
    parser.set_defaults(screenshot=None)

    group = parser.add_argument_group('Frequency, create a regular crawler/scheduler. one shot if not specified')
    group.add_argument('-f', '--frequency', type=str, choices=['monthly', 'weekly', 'daily', 'hourly'],
                       help='monthly, weekly, daily or hourly frequency or specify a custom one with the others arguments')
    group.add_argument('--minutes', type=int, help='frequency in minutes')
    group.add_argument('--hours', type=int, help='frequency in hours')
    group.add_argument('--days', type=int, help='frequency in days')
    group.add_argument('--weeks', type=int, help='frequency in weeks')
    group.add_argument('--months', type=int, help='frequency in months')

    args = parser.parse_args()

    if not args.url and not args.key:
        parser.print_help()
        sys.exit(0)

    # Load crawler default config
    config_loader = ConfigLoader()
    har = args.har
    if har is None:
        har = config_loader.get_config_boolean('Crawler', 'default_har')
    screenshot = args.screenshot
    if screenshot is None:
        screenshot = config_loader.get_config_boolean('Crawler', 'default_screenshot')

    if args.depth:
        depth = args.depth
        if depth < 0:
            raise argparse.ArgumentTypeError(f'Error: Invalid depth {depth}')
    else:
        depth = 1

    # frequency
    frequency = {}
    if args.frequency:
        if args.frequency in ['monthly', 'weekly', 'daily', 'hourly']:
            frequency = args.frequency
        else:
            raise argparse.ArgumentTypeError('Invalid frequency')
    elif args.minutes or args.hours or args.days or args.weeks or args.months:
        if args.minutes:
            check_frequency(args.minutes)
            frequency['minutes'] = args.minutes
        if args.hours:
            check_frequency(args.hours)
            frequency['hours'] = args.hours
        if args.days:
            check_frequency(args.days)
            frequency['days'] = args.days
        if args.weeks:
            check_frequency(args.weeks)
            frequency['weeks'] = args.weeks
        if args.months:
            check_frequency(args.months)
            frequency['months'] = args.months
    if not frequency:
        frequency = None

    proxy = args.proxy

    if args.cookiejar:
        cookiejar = args.cookiejar
    else:
        cookiejar = None

    ail = args.ail
    if not ail:
        ail = 'https://localhost:7000/'

    client = PyAIL(ail, args.key, ssl=False)
    r = client.crawl_url(args.url, har=har, screenshot=screenshot, depth_limit=depth, frequency=frequency,
                         cookiejar=cookiejar, proxy=proxy)
    print(r)

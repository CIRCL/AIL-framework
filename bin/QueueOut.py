#!/usr/bin/env python3
# -*-coding:UTF-8 -*

from pubsublogger import publisher
from Helper import Process
import argparse


def run(config_section):
    p = Process(config_section)
    if not p.publish():
        print(config_section, 'has no publisher.')


if __name__ == '__main__':
    publisher.port = 6380
    publisher.channel = 'Queuing'

    parser = argparse.ArgumentParser(description='Entry queue for a module.')
    parser.add_argument("-c", "--config_section", type=str,
                        help="Config section to use in the config file.")
    args = parser.parse_args()

    run(args.config_section)

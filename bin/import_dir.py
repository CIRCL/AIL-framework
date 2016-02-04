#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
import base64
import argparse
import os


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Take files from a directory and push them into a 0MQ feed.')
    parser.add_argument('-d', '--directory', type=str, required=True, help='Root directory to import')
    parser.add_argument('-p', '--port', type=int, default=5556, help='Zero MQ port')
    parser.add_argument('-c', '--channel', type=str, default='102', help='Zero MQ channel')

    args = parser.parse_args()

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:{}".format(args.port))

    for dirname, dirnames, filenames in os.walk(args.directory):
        for filename in filenames:
            messagedata = open(os.path.join(dirname, filename)).read()
            print(os.path.join(dirname, filename))
            socket.send('{} {} {}'.format(args.channel, filename, base64.b64encode(messagedata)))

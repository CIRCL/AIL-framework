#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of AIL framework - Analysis Information Leak framework
#
# This a simple feeder script feeding data from pystemon to AIL.
#
# Don't forget to set your pystemonpath and ensure that the
# configuration matches this script. Default is Redis DB 10.
#
# https://github.com/cvandeplas/pystemon/blob/master/pystemon.yaml#L16
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Copyright (c) 2014 Alexandre Dulaunoy - a@foo.be

import os
import sys

import zmq
import random
import time
import redis
import base64

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()

if config_loader.has_option("ZMQ_Global", "bind"):
    zmq_url = config_loader.get_config_str("ZMQ_Global", "bind")
else:
    zmq_url = "tcp://127.0.0.1:5556"

pystemonpath = config_loader.get_config_str("Directories", "pystemonpath")
pastes_directory = config_loader.get_config_str("Directories", "pastes")
pastes_directory = os.path.join(os.environ['AIL_HOME'], pastes_directory)
base_sleeptime = 0.01
sleep_inc = 0

config_loader = None

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(zmq_url)

# check https://github.com/cvandeplas/pystemon/blob/master/pystemon.yaml#L16
r = redis.StrictRedis(host='localhost', db=10, decode_responses=True)

# 101 pastes processed feed
# 102 raw pastes feed
topic = '102'

while True:
    time.sleep(base_sleeptime + sleep_inc)
    item_id = r.lpop("pastes")
    if item_id is None:
        continue
    try:
        print(item_id)
        full_item_path = os.path.join(pystemonpath, item_id)
        if not os.path.isfile(full_item_path):
            print('Error: {}, file not found'.format(full_item_path))
            sleep_inc = 1
            continue

        with open(full_item_path, 'rb') as f: #.read()
            messagedata = f.read()
        path_to_send = os.path.join(pastes_directory, item_id)
        path_to_send = 'pystemon>>' + path_to_send

        s = b' '.join( [ topic.encode(), path_to_send.encode(), base64.b64encode(messagedata) ] )
        socket.send(s)
        sleep_inc = sleep_inc-0.01 if sleep_inc-0.01 > 0 else 0
    except IOError as e:
        # file not found, could be a buffering issue -> increase sleeping time
        print('IOError: Increasing sleep time')
        sleep_inc += 0.5
        continue

#!/usr/bin/env python
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


import zmq
import random
import sys
import time
import redis
import base64
import os
import ConfigParser

configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
if not os.path.exists(configfile):
    raise Exception('Unable to find the configuration file. \
        Did you set environment variables? \
        Or activate the virtualenv.')

cfg = ConfigParser.ConfigParser()
cfg.read(configfile)

if cfg.has_option("ZMQ_Global", "bind"):
    zmq_url = cfg.get("ZMQ_Global", "bind")
else:
    zmq_url = "tcp://127.0.0.1:5556"

pystemonpath = cfg.get("Directories", "pystemonpath")
base_sleeptime = 0.01
sleep_inc = 0

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind(zmq_url)

# check https://github.com/cvandeplas/pystemon/blob/master/pystemon.yaml#L16
r = redis.StrictRedis(host='localhost', db=10)

# 101 pastes processed feed
# 102 raw pastes feed

while True:
    time.sleep(base_sleeptime + sleep_inc)
    topic = 101
    paste = r.lpop("pastes")
    if paste is None:
        continue
    socket.send("%d %s" % (topic, paste))
    topic = 102
    try:
        messagedata = open(pystemonpath+paste).read()
        socket.send("%d %s %s" % (topic, paste, base64.b64encode(messagedata)))
        sleep_inc = sleep_inc-0.01 if sleep_inc-0.01 > 0 else 0
    except IOError as e:
        # file not found, could be a buffering issue -> increase sleeping time
        print('IOError: Increasing sleep time')
        sleep_inc += 0.5
        continue

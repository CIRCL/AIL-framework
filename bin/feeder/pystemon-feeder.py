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

port = "5556"
pystemonpath = "/home/pystemon/pystemon/"

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)

# check https://github.com/cvandeplas/pystemon/blob/master/pystemon.yaml#L16
r = redis.StrictRedis(host='localhost', db=10)

# 101 pastes processed feed
# 102 raw pastes feed

while True:
    time.sleep(1)
    topic = 101
    paste = r.lpop("pastes")
    if paste is None:
        continue
    socket.send("%d %s" % (topic, paste))
    topic = 102
    messagedata = open(pystemonpath+paste).read()
    socket.send("%d %s %s" % (topic, paste, base64.b64encode(messagedata)))

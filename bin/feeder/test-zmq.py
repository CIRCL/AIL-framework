#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of AIL framework - Analysis Information Leak framework
#
#
# Python script to test if the ZMQ feed works as expected
#

import sys
import zmq

port = "5556"

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect ("tcp://crf.circl.lu:%s" % port)

# 101 Name of the pastes only
# 102 Full pastes in raw base64(gz)

topicfilter = "102"
socket.setsockopt_string(zmq.SUBSCRIBE, topicfilter)

while True:
    message = socket.recv()
    print('b1')
    print (message)
    if topicfilter == "102":
        topic, paste, messagedata = message.split()
        print(paste, messagedata)
    else:
        print (message)

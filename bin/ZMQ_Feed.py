#!/usr/bin/env python2
# -*-coding:UTF-8 -*
"""
The ZMQ_Feed_Q Module
=====================

This module is consuming the Redis-list created by the ZMQ_Feed_Q Module,
And save the paste on disk to allow others modules to work on them.

..todo:: Be able to choose to delete or not the saved paste after processing.
..todo:: Store the empty paste (unprocessed) somewhere in Redis.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

Requirements
------------

*Need running Redis instances.
*Need the ZMQ_Feed_Q Module running to be able to work properly.

"""
import base64
import os
import time
from pubsublogger import publisher

import Helper


if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Feed'
    config_channel = 'topicfilter'
    subscriber_name = 'feed'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    # Publisher
    pub_config_section = "PubSub_Global"
    pub_config_channel = 'channel'
    h.zmq_pub(pub_config_section, pub_config_channel)

    # LOGGING #
    publisher.info("Feed Script started to receive & publish.")

    while True:

        message = h.redis_rpop()
        # Recovering the streamed message informations.
        if message is not None:
            if len(message.split()) == 3:
                topic, paste, gzip64encoded = message.split()
                print paste
            else:
                # TODO Store the name of the empty paste inside a Redis-list.
                print "Empty Paste: not processed"
                publisher.debug("Empty Paste: {0} not processed".format(paste))
                continue
        else:
            if h.redis_queue_shutdown():
                print "Shutdown Flag Up: Terminating"
                publisher.warning("Shutdown Flag Up: Terminating.")
                break
            print "Empty Queues: Waiting..."
            time.sleep(10)
            continue
        # Creating the full filepath
        filename = os.path.join(os.environ['AIL_HOME'],
                                h.config.get("Directories", "pastes"), paste)
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(filename, 'wb') as f:
            f.write(base64.standard_b64decode(gzip64encoded))

        h.zmq_pub_send(filename)

#!/usr/bin/python2.7
"""
The ``ZMQ PubSub`` Modules
==========================

"""

import zmq, ConfigParser, redis, pprint, os, sys
#from pubsublogger import publisher

class PubSub(object):
    """
    The PubSub class is a ``Virtual Class`` which regroup the shared attribute
    of a Publisher ZeroMQ and a Subcriber ZeroMQ

    :param file_conf: -- (str) The filepath of the configuration file used (.cfg)
    :param log_channel: -- (str) The channel used as a log channel
    :param ps_name: -- (str) The "ID" of the Publisher/Subcriber

    :return: PubSub Object

    ..note:: The ps_name was implemented to separate subscriber queues in redis
    when they are listening on a same "stream"
    ..seealso:: Method of the ZMQSub class

    ..todo:: Create Implementing a log channel as an attribute of this virtual class.

    """
    def __init__(self, file_conf, log_channel, ps_name):
        self._ps_name = ps_name
        self._config_parser = ConfigParser.ConfigParser()
        self._config_file = file_conf # "./packages/config.cfg"

        self._config_parser.read(self._config_file)

        self._context_zmq = zmq.Context()

        #self._logging_publisher_channel = log_channel # "Default"
        #publisher.channel(self._logging_publisher_channel)


class ZMQPub(PubSub):
    """
    This class create a ZMQ Publisher which is able to send_message to a choosen socket.

    :param pub_config_section: -- (str) The name of the section in the config file to get the settings

    :return: ZMQPub Object

    :Example:
    Extract of the config file:
        [PubSub_Categ]
        adress = tcp://127.0.0.1:5003

    Creating the object and sending message:
        MyPublisher = ZMQPub('./packages/config.cfg', 'PubSub_Categ', 'pubcateg')

        msg = "categ1"+" "+"Im the data sent on the categ1 channel"
        MyPublisher.send_message(msg)

    ..note:: The ps_name attribute for a publisher is "optionnal" but still required to be
    instantiated correctly.

    """
    def __init__(self, file_conf, pub_config_section, ps_name):
        super(ZMQPub, self).__init__(file_conf, "Default", ps_name)

        self._pub_config_section = pub_config_section
        self._pubsocket = self._context_zmq.socket(zmq.PUB)
        self._pub_adress = self._config_parser.get(self._pub_config_section, "adress")

        self._pubsocket.bind(self._config_parser.get(self._pub_config_section, "adress"))

    def send_message(self, message):
        """Send a message throught the publisher socket"""
        self._pubsocket.send(message)


class ZMQSub(PubSub):
    """
    This class create a ZMQ Subcriber which is able to receive message directly or
    throught redis as a buffer.

    The redis buffer is usefull when the subcriber do a time consuming job which is
    desynchronising it from the stream of data received.
    The redis buffer ensures that no data will be loss waiting to be processed.

    :param sub_config_section: -- (str) The name of the section in the config file to get the settings
    :param channel: -- (str) The listening channel of the Subcriber.

    :return: ZMQSub Object

    :Example:
    Extract of the config file:
        [PubSub_Global]
        adress = tcp://127.0.0.1:5000
        channel = filelist

    Creating the object and receiving data + pushing to redis (redis buffering):

        r_serv = redis.StrictRedis(
            host = 127.0.0.1,
            port = 6387,
            db = 0)

        channel = cfg.get("PubSub_Global", "channel")
        MySubscriber = ZMQSub('./packages/config.cfg',"PubSub_Global", channel, "duplicate")

        while True:
            MySubscriber.get_and_lpush(r_serv)


    Inside another script use this line to retrive the data from redis.
        ...
        while True:
            MySubscriber.get_msg_from_queue(r_serv)
        ...

    ..note:: If you don't want any redis buffering simply use the "get_message" method

    """
    def __init__(self, file_conf, sub_config_section, channel, ps_name):
        super(ZMQSub, self).__init__(file_conf, "Default", ps_name)

        self._sub_config_section = sub_config_section
        self._subsocket = self._context_zmq.socket(zmq.SUB)
        self._sub_adress = self._config_parser.get(self._sub_config_section, "adress")

        self._subsocket.connect(self._config_parser.get(self._sub_config_section, "adress"))

        self._channel = channel
        self._subsocket.setsockopt(zmq.SUBSCRIBE, self._channel)

    def get_message(self):
        """
        Get the first sent message from a Publisher.
        :return: (str) Message from Publisher

        """
        return self._subsocket.recv()

    def get_and_lpush(self, r_serv):
        """
        Get the first sent message from a Publisher and storing it in redis

        ..note:: This function also create a set named "queue" for monitoring needs

        """
        r_serv.sadd("queues",self._channel+self._ps_name)
        r_serv.lpush(self._channel+self._ps_name, self._subsocket.recv())

    def get_msg_from_queue(self, r_serv):
        """
        Get the first sent message from a Redis List

        :return: (str) Message from Publisher

        """
        return r_serv.rpop(self._channel+self._ps_name)
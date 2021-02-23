#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Queue helper module
============================

This module subscribe to a Publisher stream and put the received messages
into a Redis-list waiting to be popped later by others scripts.

..note:: Module ZMQ_Something_Q and ZMQ_Something are closely bound, always put
the same Subscriber name in both of them.

"""
import redis
import configparser
import os
import zmq
import time
import datetime
import json


class PubSub(object): ## TODO: remove config, use ConfigLoader by default

    def __init__(self):
        configfile = os.path.join(os.environ['AIL_HOME'], 'configs/core.cfg')
        if not os.path.exists(configfile):
            raise Exception('Unable to find the configuration file. \
                            Did you set environment variables? \
                            Or activate the virtualenv.')
        self.config = configparser.ConfigParser()
        self.config.read(configfile)
        self.redis_sub = False
        self.zmq_sub = False
        self.subscribers = None
        self.publishers = {'Redis': [], 'ZMQ': []}

    def setup_subscribe(self, conn_name):
        if self.config.has_section(conn_name):
            channel = self.config.get(conn_name, 'channel')
        else:
            channel = conn_name.split('_')[1]
        if conn_name.startswith('Redis'):
            self.redis_sub = True
            r = redis.StrictRedis(
                host=self.config.get('RedisPubSub', 'host'),
                port=self.config.get('RedisPubSub', 'port'),
                db=self.config.get('RedisPubSub', 'db'),
                decode_responses=True)
            self.subscribers = r.pubsub(ignore_subscribe_messages=True)
            self.subscribers.psubscribe(channel)
        elif conn_name.startswith('ZMQ'):
            self.zmq_sub = True
            context = zmq.Context()

            # Get all feeds
            self.subscribers = []
            addresses = self.config.get(conn_name, 'address')
            for address in addresses.split(','):
                subscriber = context.socket(zmq.SUB)
                subscriber.connect(address)
                subscriber.setsockopt_string(zmq.SUBSCRIBE, channel)
                self.subscribers.append(subscriber)

    def setup_publish(self, conn_name):
        if self.config.has_section(conn_name):
            channel = self.config.get(conn_name, 'channel')
        else:
            channel = conn_name.split('_')[1]
        if conn_name.startswith('Redis'):
            r = redis.StrictRedis(host=self.config.get('RedisPubSub', 'host'),
                                  port=self.config.get('RedisPubSub', 'port'),
                                  db=self.config.get('RedisPubSub', 'db'),
                                  decode_responses=True)
            self.publishers['Redis'].append((r, channel))
        elif conn_name.startswith('ZMQ'):
            context = zmq.Context()
            p = context.socket(zmq.PUB)
            p.bind(self.config.get(conn_name, 'address'))
            self.publishers['ZMQ'].append((p, channel))

    def publish(self, message):
        m = json.loads(message)
        channel_message = m.get('channel')
        for p, channel in self.publishers['Redis']:
            if channel_message is None or channel_message == channel:
                p.publish(channel, ( m['message']) )
        for p, channel in self.publishers['ZMQ']:
            if channel_message is None or channel_message == channel:
                p.send('{} {}'.format(channel, m['message']))
                #p.send(b' '.join( [channel,  mess] ) )


    def subscribe(self):
        if self.redis_sub:
            for msg in self.subscribers.listen():
                if msg.get('data', None) is not None:
                    yield msg['data']
        elif self.zmq_sub:
            # Initialize poll set
            poller = zmq.Poller()
            for subscriber in self.subscribers:
                poller.register(subscriber, zmq.POLLIN)

            while True:
                socks = dict(poller.poll())

                for subscriber in self.subscribers:
                    if subscriber in socks:
                        message = subscriber.recv()
                        yield message.split(b' ', 1)[1]
        else:
            raise Exception('No subscribe function defined')


class Process(object):

    def __init__(self, conf_section, module=True):
        configfile = os.path.join(os.environ['AIL_HOME'], 'configs/core.cfg')
        if not os.path.exists(configfile):
            raise Exception('Unable to find the configuration file. \
                            Did you set environment variables? \
                            Or activate the virtualenv.')
        modulesfile = os.path.join(os.environ['AIL_BIN'], 'packages/modules.cfg')
        self.config = configparser.ConfigParser()
        self.config.read(configfile)
        self.modules = configparser.ConfigParser()
        self.modules.read(modulesfile)
        self.subscriber_name = conf_section

        self.pubsub = None
        if module:
            if self.modules.has_section(conf_section):
                self.pubsub = PubSub()
            else:
                raise Exception('Your process has to listen to at least one feed.')
            self.r_temp = redis.StrictRedis(
                host=self.config.get('RedisPubSub', 'host'),
                port=self.config.get('RedisPubSub', 'port'),
                db=self.config.get('RedisPubSub', 'db'),
                decode_responses=True)

            self.serv_statistics = redis.StrictRedis(
                host=self.config.get('ARDB_Statistics', 'host'),
                port=self.config.get('ARDB_Statistics', 'port'),
                db=self.config.get('ARDB_Statistics', 'db'),
                decode_responses=True)

            self.moduleNum = os.getpid()

    def populate_set_in(self):
        # monoproc
        try:
            src = self.modules.get(self.subscriber_name, 'subscribe')
        except configparser.NoOptionError: #NoSectionError
            src = None
        if src != 'Redis' and src:
            self.pubsub.setup_subscribe(src)
            for msg in self.pubsub.subscribe():
                in_set = self.subscriber_name + 'in'
                self.r_temp.sadd(in_set, msg)
                self.r_temp.hset('queues', self.subscriber_name,
                                 int(self.r_temp.scard(in_set)))
        else:
            print('{} has no subscriber'.format(self.subscriber_name))

    def get_from_set(self):
        # multiproc
        in_set = self.subscriber_name + 'in'
        self.r_temp.hset('queues', self.subscriber_name,
                         int(self.r_temp.scard(in_set)))
        message = self.r_temp.spop(in_set)

        timestamp = int(time.mktime(datetime.datetime.now().timetuple()))
        dir_name = os.environ['AIL_HOME']+self.config.get('Directories', 'pastes')

        if message is None:
            return None

        else:
            try:
                if '.gz' in message:
                    path = message.split(".")[-2].split("/")[-1]
                    #find start of path with AIL_HOME
                    index_s = message.find(os.environ['AIL_HOME'])
                    #Stop when .gz
                    index_e = message.find(".gz")+3
                    if(index_s == -1):
                        complete_path = message[0:index_e]
                    else:
                        complete_path = message[index_s:index_e]

                else:
                    path = "-"
                    complete_path = "?"

                value = str(timestamp) + ", " + path
                self.r_temp.set("MODULE_"+self.subscriber_name + "_" + str(self.moduleNum), value)
                self.r_temp.set("MODULE_"+self.subscriber_name + "_" + str(self.moduleNum) + "_PATH", complete_path)
                self.r_temp.sadd("MODULE_TYPE_"+self.subscriber_name, str(self.moduleNum))

                curr_date = datetime.date.today()
                self.serv_statistics.hincrby(curr_date.strftime("%Y%m%d"),'paste_by_modules_in:'+self.subscriber_name, 1)
                return message

            except:
                print('except')
                path = "?"
                value = str(timestamp) + ", " + path
                self.r_temp.set("MODULE_"+self.subscriber_name + "_" + str(self.moduleNum), value)
                self.r_temp.set("MODULE_"+self.subscriber_name + "_" + str(self.moduleNum) + "_PATH", "?")
                self.r_temp.sadd("MODULE_TYPE_"+self.subscriber_name, str(self.moduleNum))
                return message

    def populate_set_out(self, msg, channel=None):
        # multiproc
        msg = {'message': msg}
        if channel is not None:
            msg.update({'channel': channel})

        # bytes64 encode bytes to ascii only bytes
        j = json.dumps(msg)
        self.r_temp.sadd(self.subscriber_name + 'out', j)

    def publish(self):
        # monoproc
        if not self.modules.has_option(self.subscriber_name, 'publish'):
            return False
        dest = self.modules.get(self.subscriber_name, 'publish')
        # We can have multiple publisher
        for name in dest.split(','):
            self.pubsub.setup_publish(name)
        while True:
            message = self.r_temp.spop(self.subscriber_name + 'out')

            if message is None:
                time.sleep(1)
                continue
            self.pubsub.publish(message)

    def incr_module_timeout_statistic(self):
        curr_date = datetime.date.today()
        self.serv_statistics.hincrby(curr_date.strftime("%Y%m%d"),'paste_by_modules_timeout:'+self.subscriber_name, 1)

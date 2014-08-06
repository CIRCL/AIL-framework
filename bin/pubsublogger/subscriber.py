#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
:mod:`subscriber` -- Subscribe to a redis channel and gather logging messages.

To use this module, you have to define at least a channel name.
"""


import redis
from logbook import Logger
import ConfigParser
from logbook import NestedSetup, NullHandler, FileHandler, MailHandler
import os

# use a TCP Socket by default
use_tcp_socket = True

#default config for a UNIX socket
unix_socket = '/tmp/redis.sock'
# default config for a TCP socket
hostname = 'localhost'
port = 6379

pubsub = None
channel = None

# Required only if you want to send emails
dest_mails = []
smtp_server = None
smtp_port = 0
src_server = None

def setup(name, path = 'log', enable_debug = False):
    """
    Prepare a NestedSetup.

    :param name: the channel name
    :param path: the path where the logs will be written
    :param enable_debug: do we want to save the message at the DEBUG level

    :return a nested Setup
    """
    path_tmpl = os.path.join(path, '{name}_{level}.log')
    info = path_tmpl.format(name = name, level = 'info')
    warn = path_tmpl.format(name = name, level = 'warn')
    err = path_tmpl.format(name = name, level = 'err')
    crit = path_tmpl.format(name = name, level = 'crit')
    # a nested handler setup can be used to configure more complex setups
    setup = [
        # make sure we never bubble up to the stderr handler
        # if we run out of setup handling
        NullHandler(),
        # then write messages that are at least info to to a logfile
        FileHandler(info, level='INFO', encoding='utf-8'),
        # then write messages that are at least warnings to to a logfile
        FileHandler(warn, level='WARNING', encoding='utf-8'),
        # then write messages that are at least errors to to a logfile
        FileHandler(err, level='ERROR', encoding='utf-8'),
        # then write messages that are at least critical errors to to a logfile
        FileHandler(crit, level='CRITICAL', encoding='utf-8'),
    ]
    if enable_debug:
        debug = path_tmpl.format(name = name, level = 'debug')
        setup.insert(1, FileHandler(debug, level='DEBUG', encoding='utf-8'))
    if src_server is not None and smtp_server is not None \
            and smtp_port != 0 and len(dest_mails) != 0:
        mail_tmpl = '{name}_error@{src}'
        from_mail = mail_tmpl.format(name = name, src = src_server)
        subject = 'Error in {}'.format(name)
        # errors should then be delivered by mail and also be kept
        # in the application log, so we let them bubble up.
        setup.append(MailHandler(from_mail, dest_mails, subject,
            level='ERROR', bubble=True, server_addr=(smtp_server, smtp_port)))

    return NestedSetup(setup)

def mail_setup(path):
    """
    Set the variables to be able to send emails.

    :param path: path to the config file
    """
    global dest_mails
    global smtp_server
    global smtp_port
    global src_server
    config = ConfigParser.RawConfigParser()
    config.readfp(path)
    dest_mails = config.get('mail', 'dest_mail').split(',')
    smtp_server = config.get('mail', 'smtp_server')
    smtp_port = config.get('mail', 'smtp_port')
    src_server = config.get('mail', 'src_server')

def run(log_name, path, debug = False, mail = None):
    """
    Run a subscriber and pass the messages to the logbook setup.
    Stays alive as long as the pubsub instance listen to something.

    :param log_name: the channel to listen to
    :param path: the path where the log files will be written
    :param debug: True if you want to save the debug messages too
    :param mail: Path to the config file for the mails

    """
    global pubsub
    global channel
    channel = log_name
    if use_tcp_socket:
        r = redis.StrictRedis(host=hostname, port=port)
    else:
        r = redis.StrictRedis(unix_socket_path = unix_socket)
    pubsub = r.pubsub()
    pubsub.psubscribe(channel + '.*')

    logger = Logger(channel)
    if mail is not None:
        mail_setup(mail)
    if os.path.exists(path) and not os.path.isdir(path):
        raise Exception("The path you want to use to save the file is invalid (not a directory).")
    if not os.path.exists(path):
        os.mkdir(path)
    with setup(channel, path, debug):
        for msg in pubsub.listen():
            if msg['type'] == 'pmessage':
                level = msg['channel'].split('.')[1]
                message = msg['data']
                try:
                    message = message.decode('utf-8')
                except:
                    pass
                logger.log(level, message)


def stop():
    """
    Unsubscribe to the channel, stop the script.
    """
    pubsub.punsubscribe(channel + '.*')

#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    PgpDum module

    Extract ID from PGP Blocks
"""

import os
import re
import time
import uuid
import redis
import signal
import datetime
import subprocess

from pubsublogger import publisher
from bs4 import BeautifulSoup

from Helper import Process
from packages import Paste

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)

# save pgp message in directory, process one time each day
def save_in_file(message, pgp_content):
    print('save in file')
    UUID = str(uuid.uuid4())
    file_name = os.path.join(pgp_dump_dir_to_process, UUID)
    with open(file_name, 'w') as f:
        f.write(pgp_content)
    r_serv_db.sadd('pgpdumb:uuid', '{};{}'.format(UUID, message))

def remove_html(item_content):
    if bool(BeautifulSoup(item_content, "html.parser").find()):
        soup = BeautifulSoup(item_content, 'html.parser')
        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()    # remove

        # get text
        text = soup.get_text()
        return text
    else:
        return item_content

def extract_all_id(message, item_content, regex=None, is_file=False):

    if is_file:
        pgp_packet = get_pgp_packet_file(item_content)
        extract_id_from_output(pgp_packet)

    else:
        # max execution time on regex
        signal.alarm(max_execution_time)
        try:
            pgp_extracted_block = re.findall(regex, item_content)
        except TimeoutException:
            pgp_extracted_block = []
            p.incr_module_timeout_statistic() # add encoder type
            print ("{0} processing timeout".format(paste.p_rel_path))
        else:
            signal.alarm(0)

        for pgp_to_dump in pgp_extracted_block:
            pgp_packet = get_pgp_packet(message, pgp_to_dump)
            extract_id_from_output(pgp_packet)

def get_pgp_packet(message, save_path):
    save_path = '{}'.format(save_path)
    if len(save_path) > 131072:
        save_in_file(message, save_path)
        return ''
    else:
        process1 = subprocess.Popen([ 'echo', '-e', save_path], stdout=subprocess.PIPE)
        process2 = subprocess.Popen([ 'pgpdump'], stdin=process1.stdout, stdout=subprocess.PIPE)
        process1.stdout.close()
        output = process2.communicate()[0]
        try:
            output = output.decode()
        except UnicodeDecodeError:
            publisher.error('Error PgpDump UnicodeDecodeError: {}'.format(message))
            output = ''
        return output

def get_pgp_packet_file(file):
    process1 = subprocess.Popen([ 'pgpdump', file], stdout=subprocess.PIPE)
    output = process1.communicate()[0].decode()
    return output

def extract_id_from_output(pgp_dump_outpout):
    all_user_id = set(re.findall(regex_user_id, pgp_dump_outpout))
    for user_id in all_user_id:
        # avoid key injection in user_id:
        pgp_dump_outpout.replace(user_id, '', 1)

        user_id = user_id.replace(user_id_str, '', 1)
        mail = None
        if ' <' in user_id:
            name, mail = user_id.rsplit(' <', 1)
            mail = mail[:-1]
            set_name.add(name)
            set_mail.add(mail)
        else:
            name = user_id
            set_name.add(name)

    all_key_id = set(re.findall(regex_key_id, pgp_dump_outpout))
    for key_id in all_key_id:
        key_id = key_id.replace(key_id_str, '', 1)
        set_key.add(key_id)

def save_pgp_data(type_pgp, date, item_path, data):
    # create basic medata
    if not serv_metadata.exists('pgpdump_metadata_{}:{}'.format(type_pgp, data)):
        serv_metadata.hset('pgpdump_metadata_{}:{}'.format(type_pgp, data), 'first_seen', date)
        serv_metadata.hset('pgpdump_metadata_{}:{}'.format(type_pgp, data), 'last_seen', date)
    else:
        last_seen = serv_metadata.hget('pgpdump_metadata_{}:{}'.format(type_pgp, data), 'last_seen')
        if not last_seen:
            serv_metadata.hset('pgpdump_metadata_{}:{}'.format(type_pgp, data), 'last_seen', date)
        else:
            if int(last_seen) < int(date):
                serv_metadata.hset('pgpdump_metadata_{}:{}'.format(type_pgp, data), 'last_seen', date)

    # global set
    serv_metadata.sadd('set_pgpdump_{}:{}'.format(type_pgp, data), item_path)

    # daily
    serv_metadata.hincrby('pgpdump:{}:{}'.format(type_pgp, date), data, 1)

    # all type
    serv_metadata.zincrby('pgpdump_all:{}'.format(type_pgp), data, 1)

    # item_metadata
    serv_metadata.sadd('item_pgpdump_{}:{}'.format(type_pgp, item_path), data)


if __name__ == '__main__':
    # If you wish to use an other port of channel, do not forget to run a subscriber accordingly (see launch_logs.sh)
    # Port of the redis instance used by pubsublogger
    publisher.port = 6380
    # Script is the default channel used for the modules.
    publisher.channel = 'Script'

    # Section name in bin/packages/modules.cfg
    #config_section = 'PgpDump'
    config_section = 'PgpDump'

    # Setup the I/O queues
    p = Process(config_section)

    r_serv_db = redis.StrictRedis(
        host=p.config.get("ARDB_DB", "host"),
        port=p.config.getint("ARDB_DB", "port"),
        db=p.config.getint("ARDB_DB", "db"),
        decode_responses=True)

    serv_metadata = redis.StrictRedis(
        host=p.config.get("ARDB_Metadata", "host"),
        port=p.config.getint("ARDB_Metadata", "port"),
        db=p.config.getint("ARDB_Metadata", "db"),
        decode_responses=True)

    # Sent to the logging a description of the module
    publisher.info("PgpDump started")

    # check/create pgpdump queue directory (used for huge pgp blocks)
    pgp_dump_dir_to_process = os.path.join(os.environ['AIL_HOME'], 'temp', 'pgpdump')
    if not os.path.isdir(pgp_dump_dir_to_process):
        os.makedirs(pgp_dump_dir_to_process)

    user_id_str = 'User ID - '
    regex_user_id= '{}.+'.format(user_id_str)

    key_id_str = 'Key ID - '
    regex_key_id = '{}.+'.format(key_id_str)
    regex_pgp_public_blocs = '-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]+?-----END PGP PUBLIC KEY BLOCK-----'
    regex_pgp_signature = '-----BEGIN PGP SIGNATURE-----[\s\S]+?-----END PGP SIGNATURE-----'
    regex_pgp_message = '-----BEGIN PGP MESSAGE-----[\s\S]+?-----END PGP MESSAGE-----'

    re.compile(regex_user_id)
    re.compile(regex_key_id)
    re.compile(regex_pgp_public_blocs)
    re.compile(regex_pgp_signature)
    re.compile(regex_pgp_message)

    max_execution_time = p.config.getint("PgpDump", "max_execution_time")

    # Endless loop getting messages from the input queue
    while True:

        is_file = False
        set_key = set()
        set_name = set()
        set_mail = set()

        if r_serv_db.scard('pgpdumb:uuid') > 0:
            res = r_serv_db.spop('pgpdumb:uuid')
            file_to_process, message = res.split(';', 1)
            file_to_process = os.path.join(pgp_dump_dir_to_process, file_to_process)
            date = datetime.datetime.now().strftime("%Y/%m/%d")
            paste = Paste.Paste(message)
            date = str(paste._get_p_date())
            print(message)
            extract_all_id(message, file_to_process, is_file=True)
            os.remove(file_to_process)

        else:
            # Get one message from the input queue
            message = p.get_from_set()

            if message is None:
                publisher.debug("{} queue is empty, waiting".format(config_section))
                time.sleep(1)
                continue

            paste = Paste.Paste(message)

            date = str(paste._get_p_date())
            content = paste.get_p_content()
            content = remove_html(content)

            print(message)

            extract_all_id(message, content, regex_pgp_public_blocs)
            extract_all_id(message, content, regex_pgp_signature)
            extract_all_id(message, content, regex_pgp_message)

        for key_id in set_key:
            print(key_id)
            save_pgp_data('key', date, message, key_id)

        for name_id in set_name:
            print(name_id)
            save_pgp_data('name', date, message, name_id)

        for mail_id in set_mail:
            print(mail_id)
            save_pgp_data('mail', date, message, mail_id)

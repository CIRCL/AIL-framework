#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from pymisp import MISPObject

import requests


sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects
from lib.ConfigLoader import ConfigLoader
from lib import crawlers
from lib.objects import Domains
from lib.objects import IPAddresses
from packages import git_status
from packages import Date
# from lib.data_retention_engine import update_obj_date, get_obj_date_first

from flask import url_for

config_loader = ConfigLoader()
r_db = config_loader.get_db_conn("Kvrocks_DB")
r_object = config_loader.get_db_conn("Kvrocks_Objects")
r_cache = config_loader.get_redis_conn("Redis_Cache")
baseurl = config_loader.get_config_str("Notifications", "ail_domain")

save_har = config_loader.get_config_boolean('Crawler', 'default_har')
save_screenshot = config_loader.get_config_boolean('Crawler', 'default_screenshot')
config_loader = None


class SSHKey(AbstractDaterangeObject):
    """
    AIL SSHKey Object. (strings)
    """

    def __init__(self, id):
        super(SSHKey, self).__init__('ssh-key', id)

    def get_date(self):
        return Date.get_today_date_str()

    def get_nb_seen(self):
        return self.get_nb_correlation('domain')

    def get_source(self):  # TODO remove ME
        """
        Returns source/feeder name
        """
        return 'ssh-key'

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'fas', 'icon': '\uf120', 'color': 'grey', 'radius': 5}

    def get_misp_object(self):  # TODO
        obj = MISPObject('passive-ssh', standalone=True)
        first_seen = self.get_first_seen()
        last_seen = self.get_last_seen()
        if not first_seen:
            first_seen = self.get_date()
            last_seen = first_seen
        obj.first_seen = first_seen
        obj.last_seen = last_seen
        # TODO host (s)
        # TODO base64 key
        # TODO banner
        # hassh ???
        obj_attrs = [obj.add_attribute('first-seen', value=first_seen),
                     obj.add_attribute('last_seen', value=last_seen),
                     obj.add_attribute('fingerprint', value=self.id)]
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_key_type(self):
        return self._get_field('type')

    def set_key_type(self, key_type):
        self._set_field('type', key_type)

    # options: set of optional meta fields
    def get_meta(self, options=None):  # TODO get HOSTS
        """
        :type options: set
        """
        if options is None:
            options = set()
        meta = self._get_meta(options=options)
        meta['tags'] = self.get_tags()
        meta['content'] = self.get_content()
        meta['key_type'] = self.get_key_type()

        # optional meta fields
        if 'investigations' in options:
            meta['investigations'] = self.get_investigations()
        if 'link' in options:
            meta['link'] = self.get_link(flask_context=True)
        if 'icon' in options:
            meta['svg_icon'] = self.get_svg_icon()
        return meta

    def create(self, key_type, tags=[]):
        self._add_create()
        self.set_key_type(key_type)
        for tag in tags:
            self.add_tag(tag)
        return self.id

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self): # TODO DELETE CORRELATION
        self._delete()
        self.delete_dates()
        r_object.srem(f'{self.type}:all', self.id)


def create(fingerprint, key_type, tags=[]):
    fingerprint = fingerprint.strip()
    obj = SSHKey(fingerprint)
    if not obj.exists():
        obj.create(key_type, tags=tags)
    else:
        obj.set_key_type(key_type)
    return obj

class SSHKeys(AbstractDaterangeObjects):
    """
       SSHKeyss Objects
    """
    def __init__(self):
        super().__init__('ssh-key', SSHKey)

    def get_name(self):
        return 'SSHKeys'

    def get_icon(self):
        return {'fa': 'fab', 'icon': 'console'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_ssh.objects_ssh_keys')
        else:
            url = f'{baseurl}/objects/ssh-keys'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search.lower()

def _remove_all_objects():
    for obj in SSHKeys().get_iterator():
        obj.delete()

#### PASSIVE SSH ####

# TODO check 429 -> Too Many Requests
def set_default_passive_ssh():
    set_passive_ssh_url('https://pssh.circl.lu')
    set_passive_ssh_auth('ail-project', 'pXd/r8AnoC0zyl+kVQCwBO63khHv0Dt2owKp5Bvw9oc=')
    enable_passive_ssh()


# TODO CACHE IT
def is_passive_ssh_enabled(): # TODO
    return r_db.hget('passive-ssh', 'enabled') == 'True'

def enable_passive_ssh():
    r_db.hset('passive-ssh', 'enabled', 'True')

def disable_passive_ssh():
    r_db.hset('passive-ssh', 'enabled', 'False')

def get_passive_ssh_url():
    return r_db.hget('passive-ssh', 'url')

def set_passive_ssh_url(url):
    r_db.hset('passive-ssh', 'url', url)

def _get_passive_ssh_user():
    return r_db.hget('passive-ssh', 'user')

def _get_passive_ssh_api_password():
    return r_db.hget('passive-ssh', 'password')

def set_passive_ssh_auth(user, password):
    if not user:
        r_db.hdel('passive-ssh', 'user')
    else:
        r_db.hset('passive-ssh', 'user', user)
    if not password:
        r_db.hdel('passive-ssh', 'password')
    else:
        r_db.hset('passive-ssh', 'password', password)

def get_passive_ssh_auth():
    user = _get_passive_ssh_user()
    password = _get_passive_ssh_api_password()
    if user and password:
        return user, password
    else:
        return None

def get_passive_ssh_test():
    return r_db.hget('passive-ssh', 'test')

def set_passive_ssh_test(text, is_error=False):
    r_db.hset('passive-ssh', 'test', text)
    if is_error:
        r_db.hset('passive-ssh', 'error', 1)
    else:
        r_db.hset('passive-ssh', 'error', 0)

def get_passive_ssh_meta():
    return {'is_enabled': is_passive_ssh_enabled(),
            'url': get_passive_ssh_url(),
            'user': _get_passive_ssh_user(),
            'password': _get_passive_ssh_api_password(),
            'test': get_passive_ssh_test()}

def get_passive_ssh_session():
    s = requests.Session()
    passive_ssh_auth = get_passive_ssh_auth()
    if passive_ssh_auth:
        s.auth = passive_ssh_auth
    commit_id = git_status.get_last_commit_id_from_local()
    s.headers.update({'User-Agent': f'AIL-{commit_id}'})
    return s

# TODO
#       stats ??
#
#   - domain - ssh
#   - domain - history
#   - fingerprint - hosts
#   - hassh - hosts

def _get_passive_ssh_result(path):
    s = get_passive_ssh_session()
    res = s.get(f'{get_passive_ssh_url()}{path}')
    if res.status_code != 200:
        # TODO LOG
        if res.status_code != 404:
            print(f" PassiveSSH requests error: {res.status_code}, {res.text}")
        # set_passive_ssh_test(f"{res.status_code}: {res.text}", is_error=True)
        return res.text, res.status_code
    else:
        r = res.json()
        if r:
            return r, 200
    return None, 200

def get_passive_ssh_host(domain):
    res = _get_passive_ssh_result(f'/host/ssh/{domain}')
    if res[1] == 200:
        return res[0]
    else:
        return None

def get_passive_ssh_host_history(domain):
    res = _get_passive_ssh_result(f'/host/history/{domain}')
    if res[1] == 200:
        return res[0]
    else:
        return None

def get_passive_ssh_fingerprint_hosts(fingerprint):
    res = _get_passive_ssh_result(f'/fingerprint/all/{fingerprint}')
    if res[1] == 200:
        return res[0]
    else:
        return None

def get_passive_ssh_fingerprint_ips(fingerprint):
    res = get_passive_ssh_fingerprint_hosts(fingerprint)
    if not res:
        return []
    hosts = []
    for host in res.get('hosts', []):
        if not host.endswith('.onion'):
            hosts.append(host)
    return hosts

def save_passive_ssh_fingerprint_ips(fingerprint):
    hosts = get_passive_ssh_fingerprint_ips(fingerprint)
    date = Date.get_today_date_str()
    for host in hosts:
        print(host)
        ip = IPAddresses.sanitize_ip(host)
        if ip:
            obj = IPAddresses.create(ip)
            obj.add(date, SSHKey(fingerprint))

def load_fingerprint_ips():
    for ssh_key in SSHKeys().get_iterator():
        save_passive_ssh_fingerprint_ips(ssh_key.get_id())

def get_passive_ssh_hassh_hosts(hassh):
    res = _get_passive_ssh_result(f'/hassh/hosts/{hassh}')
    if res[1] == 200:
        return res[0]
    else:
        return None

def save_passive_ssh_host(domain):
    # TODO check if host enabled
    ssh_host = get_passive_ssh_host(domain)
    if ssh_host:
        # TODO banner
        for key in ssh_host.get('keys', []):
            print(key)
            obj = create(key['fingerprint'], key['type'])
            obj.add(Date.get_today_date_str(), None)
            obj.add_correlation('domain', '', domain)
            # TODO content -> base64 key
            save_passive_ssh_fingerprint_ips(key)

def load_ssh_correlation():
    for domain_id in Domains.get_domains_up_by_type('onion'):
        save_passive_ssh_host(domain_id)

#### API ####

def api_test_passive_ssh():
    url = get_passive_ssh_url()
    if not url:
        return {"status": "error", "reason": "Invalid passive SSH URL"}, 400
    s = get_passive_ssh_session()
    res = s.get(f'{url}/host/ssh/ail-project.org')
    if res.status_code != 200:
        # TODO LOG
        print(f" PassiveSSH requests error: {res.status_code}, {res.text}")
        set_passive_ssh_test(f"{res.status_code}: {res.text}", is_error=True)
    else:
        set_passive_ssh_test('It works!')
    return None, 200

def api_get_passive_ssh_host(domain):  # TODO domain / IPv4 and IPv6
    if crawlers.is_valid_onion_domain(domain):
        save_passive_ssh_host(domain)
        dom = Domains.Domain(domain)
        if not dom.exists():
            if crawlers.is_crawler_activated():
                crawlers.create_task(domain, parent='discovery', priority=0, har=save_har, screenshot=save_screenshot)
    return _get_passive_ssh_result(f'/host/ssh/{domain}')

def api_get_passive_ssh_host_history(domain):  # / domain / IPv4 and IPv6
    if crawlers.is_valid_onion_domain(domain):
        save_passive_ssh_host(domain)
        dom = Domains.Domain(domain)
        if not dom.exists():
            if crawlers.is_crawler_activated():
                crawlers.create_task(domain, parent='discovery', priority=0, har=save_har, screenshot=save_screenshot)
    return _get_passive_ssh_result(f'/host/history/{domain}')

def api_get_passive_ssh_fingerprint_hosts(fingerprint):  # TODO check fingerprint
    return _get_passive_ssh_result(f'/fingerprint/all/{fingerprint}')

def api_get_passive_ssh_hassh_hosts(hassh):  # TODO check hassh
    return _get_passive_ssh_result(f'/hassh/hosts/{hassh}')

#### API ####
def api_get_ssh_key(obj_id):
    obj = SSHKey(obj_id)
    if not obj.exists():
        return {"status": "error", "reason": "Unknown SSH Key"}, 404
    meta = obj.get_meta({'content', 'icon', 'link'})
    return meta, 200

def api_edit_passive_ssh(url, user, password):
    set_passive_ssh_url(url)
    if user or password:
        set_passive_ssh_auth(user, password)
    return None, 200

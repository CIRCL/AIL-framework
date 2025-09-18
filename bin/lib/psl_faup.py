#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import idna
import ipaddress
import socket

from publicsuffixlist import PublicSuffixList
from urllib.parse import urlparse, urlunparse

ADDED_TLD = {'b32.i2p'}

def _ensure_bytes(binary):
    if isinstance(binary, bytes):
        return binary
    else:
        return binary.encode('utf-8')


def _ensure_str(string):
    if isinstance(string, str):
        return string
    else:
        return string.decode('utf-8')


class UrlNotDecoded(Exception):
    pass


# https://github.com/MISP/PyMISP/blob/main/pymisp/tools/_psl_faup.py
class PSLFaup:
    """
    Fake Faup Python Library using PSL for Windows support
    """

    def __init__(self):
        self.decoded = False
        self.psl = PublicSuffixList()
        self._url = None
        self._retval = {}
        self.ip_as_host = ''
        self.host = None
        self.tld = None

    def _clear(self):
        self.decoded = False
        self._url = None
        self._retval = {}
        self.ip_as_host = ''

    def decode(self, url):
        """
        This function creates a dict of all the url fields.
        :param url: The URL to normalize
        """
        self._clear()
        if isinstance(url, bytes) and b'//' not in url[:10]:
            if b'.onion' in url or b'.i2p':
                url = b'http://' + url
            else:
                url = b'https://' + url
        elif '//' not in url[:10]:
            if '.onion' in url or '.i2p' in url:
                url = f'http://{url}'
            else:
                url = f'https://{url}'
        self._url = urlparse(url)  # ValueError('%r does not appear to be an IPv4 or IPv6 address'

        if self._url is None:
            raise UrlNotDecoded("Unable to parse URL")

        self.ip_as_host = ''
        if self._url.hostname is None:
            raise UrlNotDecoded("Unable to parse URL")
        hostname = _ensure_str(self._url.hostname)
        try:
            ipv4_bytes = socket.inet_aton(hostname)
            ipv4 = ipaddress.IPv4Address(ipv4_bytes)
            self.ip_as_host = ipv4.compressed
        except (OSError, ValueError):
            try:
                addr, _, _ = hostname.partition('%')
                ipv6 = ipaddress.IPv6Address(addr)
                self.ip_as_host = ipv6.compressed
            except ValueError:
                pass

        self.decoded = True
        self._retval = {}
        self.host = self.get_host()

    @property
    def url(self):
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")

        if host := self.get_host():
            netloc = host + ('' if self.get_port() is None else f':{self.get_port()}')
            return _ensure_bytes(
                urlunparse(
                    (self.get_scheme(), netloc, self.get_resource_path(),
                     '', self.get_query_string(), self.get_fragment(),)
                )
            )
        return None

    def get_credential(self):
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")

        if self._url.username and self._url.password:
            return _ensure_str(self._url.username) + ':' + _ensure_str(self._url.password)
        if self._url.username:
            return _ensure_str(self._url.username)
        return None

    def get_scheme(self):
        """
        Get the scheme of the url given in the decode function
        :returns: The URL scheme
        """
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")
        return _ensure_str(self._url.scheme if self._url.scheme else '')

    def get_host(self):
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")

        if self.host:
            return self.host

        if self._url.hostname is None:
            return None
        elif self._url.hostname.isascii():
            return _ensure_str(self._url.hostname)
        else:
            return _ensure_str(idna.encode(self._url.hostname, uts46=True))

    def get_domain(self):
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")
        if self.ip_as_host:
            return self.ip_as_host

        if self.host is not None:
            domain = self.host[:-(len(self.get_tld()) + 1)].rsplit('.', 1)[-1]
            if domain:
                return f'{domain}.{self.tld}'
            # return self.psl.privatesuffix(self.host)
        return None

    def get_domain_without_tld(self):
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")

        if self.get_tld() is not None and not self.ip_as_host:
            if domain := self.get_domain():
                return domain.rsplit(self.tld, 1)[0].rstrip('.')
        return None

    def get_subdomain(self):
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")

        if self.host is not None and not self.ip_as_host:
            domain = self.get_domain()
            if domain and self.host and domain in self.host:
                return self.host.rsplit(domain, 1)[0].rstrip('.') or None
        return None

    def get_tld(self):
        if self.tld:
            return self.tld

        if self.host is not None and not self.ip_as_host:
            for added_tld in ADDED_TLD:
                if self.host.endswith(added_tld):
                    self.tld = added_tld
                    return added_tld
            self.tld = self.psl.publicsuffix(self.host)
            return self.tld
        return None

    def get_port(self):
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")
        try:
            return self._url.port
        except ValueError:
            return None

    def get_resource_path(self):
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")

        return _ensure_str(self._url.path)

    def get_query_string(self):
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")

        return _ensure_str(self._url.query)

    def get_fragment(self):
        if not self.decoded or not self._url:
            raise UrlNotDecoded("You must call pslfaup.decode() first")

        return _ensure_str(self._url.fragment)

    def get(self):
        self._retval["scheme"] = self.get_scheme()
        self._retval["tld"] = self.get_tld()
        self._retval["domain"] = self.get_domain()
        # self._retval["domain_without_tld"] = self.get_domain_without_tld()
        self._retval["subdomain"] = self.get_subdomain()
        self._retval["host"] = self.host
        self._retval["port"] = self.get_port()
        self._retval["resource_path"] = self.get_resource_path()
        self._retval["query_string"] = self.get_query_string()
        self._retval["fragment"] = self.get_fragment()
        self._retval["url"] = self.url
        return self._retval


def get_domain(url):
    f = PSLFaup()
    f.decode(url)
    return f.get_domain()

def get_url(url):
    f = PSLFaup()
    f.decode(url)
    return f.url

def unparse_url(url):
    f = PSLFaup()
    f.decode(url)
    return f.get()


if __name__ == '__main__':
    print(unparse_url('http://www.TEST.github.io'))

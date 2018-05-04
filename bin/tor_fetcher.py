#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import socks
import socket
import urllib.request
import io
import gzip
import base64
import sys
import tempfile

# Max size in Mb
max_size = 5

def create_connection(address, timeout=None, source_address=None):
    sock = socks.socksocket()
    sock.connect(address)
    return sock


def get_page(url, torclient_host='127.0.0.1', torclient_port=9050):

    request = urllib.request.Request(url)
    # UA of the Tor browser bundle
    request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:24.0) Gecko/20100101 Firefox/24.0')
    return urllib.request.urlopen(request, timeout=5).read(max_size * 100000)

#FIXME don't work at all
def makegzip64(s):

    out = io.BytesIO()

    with gzip.GzipFile(fileobj=out, mode='ab') as fo:
        fo.write(base64.standard_b64encode(s))

    return out.getvalue()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print('usage:', 'tor_fetcher.py', 'URL (base64 encoded)')
        exit(1)

    try:
        url = base64.standard_b64decode(sys.argv[1]).decode('utf8')
        print(url)
    except:
        print('unable to decode')
        exit(1)

    torclient_host = '127.0.0.1'
    torclient_port = 9050
    # Setup Proxy
    socks.set_default_proxy(socks.SOCKS5, torclient_host, torclient_port, True)
    socket.socket = socks.socksocket
    socket.create_connection = create_connection

    try:
        page = get_page(url)
    except:
        print('unable to fetch')
        exit(1)

    to_write = makegzip64(page)
    t, path = tempfile.mkstemp()
    #with open(path,  'w') as f:
        #f.write(to_write)
    print(path)
    exit(0)

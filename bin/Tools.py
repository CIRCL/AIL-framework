#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Tools Module
============================

Search tools outpout

"""

from Helper import Process
from pubsublogger import publisher

import os
import re
import sys
import time
import redis
import signal

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Item


class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException

signal.signal(signal.SIGALRM, timeout_handler)


def search_tools(item_id, item_content):

    tools_in_item = False

    for tools_name in tools_dict:
        tool_dict = tools_dict[tools_name]

        regex_match = False
        for regex_nb in list(range(tool_dict['nb_regex'])):
            regex_index = regex_nb + 1
            regex = tool_dict['regex{}'.format(regex_index)]

            signal.alarm(tool_dict['max_execution_time'])
            try:
                tools_found = re.findall(regex, item_content)
            except TimeoutException:
                tools_found = []
                p.incr_module_timeout_statistic() # add encoder type
                print ("{0} processing timeout".format(item_id))
                continue
            else:
                signal.alarm(0)


            if not tools_found:
                regex_match = False
                break
            else:
                regex_match = True
                if 'tag{}'.format(regex_index) in tool_dict:
                    print('{} found: {}'.format(item_id, tool_dict['tag{}'.format(regex_index)]))
                    msg = '{};{}'.format(tool_dict['tag{}'.format(regex_index)], item_id)
                    p.populate_set_out(msg, 'Tags')

        if regex_match:
            print('{} found: {}'.format(item_id, tool_dict['name']))
            # Tag Item
            msg = '{};{}'.format(tool_dict['tag'], item_id)
            p.populate_set_out(msg, 'Tags')


    if tools_in_item:
        # send to duplicate module
        p.populate_set_out(item_id, 'Duplicate')


default_max_execution_time = 30

tools_dict = {
    'sqlmap': {
        'name': 'sqlmap',
        'regex1': r'Usage of sqlmap for attacking targets without|all tested parameters do not appear to be injectable|sqlmap identified the following injection point|Title:[^\n]*((error|time|boolean)-based|stacked queries|UNION query)',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="sqlmap-tool"', # tag if all regex match
    },
    'wig': {
        'name': 'wig',
        'regex1': r'(?s)wig - WebApp Information Gatherer.+?_{10,}',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="wig-tool"', # tag if all regex match
    },
    'dmytry': {
        'name': 'dmitry',
        'regex1': r'(?s)Gathered (TCP Port|Inet-whois|Netcraft|Subdomain|E-Mail) information for.+?-{10,}',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dmitry-tool"', # tag if all regex match
    },
    'inurlbr': {
        'name': 'inurlbr',
        'regex1': r'Usage of INURLBR for attacking targets without prior mutual consent is illegal',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="inurlbr-tool"', # tag if all regex match
    },
    'wafw00f': {
        'name': 'wafw00f',
        'regex1': r'(?s)WAFW00F - Web Application Firewall Detection Tool.+?Checking',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="wafw00f-tool"', # tag if all regex match
    },
    'sslyze': {
        'name': 'sslyze',
        'regex1': r'(?s)PluginSessionRenegotiation.+?SCAN RESULTS FOR',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="sslyze-tool"', # tag if all regex match
    },
    'nmap': {
        'name': 'nmap',
        'regex1': r'(?s)Nmap scan report for.+?Host is',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="nmap-tool"', # tag if all regex match
    },
    'dnsenum': {
        'name': 'dnsenum',
        'regex1': r'(?s)dnsenum(\.pl)? VERSION:.+?Trying Zone Transfer',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dnsenum-tool"', # tag if all regex match
    },
    'knock': {
        'name': 'knock',
        'regex1': r'I scannig with my internal wordlist',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="knock-tool"', # tag if all regex match
    },
    'nikto': {
        'name': 'nikto',
        'regex1': r'(?s)\+ Target IP:.+?\+ Start Time:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="nikto-tool"', # tag if all regex match
    },
    'dnscan': {
        'name': 'dnscan',
        'regex1': r'(?s)\[\*\] Processing domain.+?\[\+\] Getting nameservers.+?records found',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dnscan-tool"', # tag if all regex match
    },
    'dnsrecon': {
        'name': 'dnsrecon',
        'regex1': r'Performing General Enumeration of Domain:|Performing TLD Brute force Enumeration against',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dnsrecon-tool"', # tag if all regex match
    },
    'striker': {
        'name': 'striker',
        'regex1': r'Crawling the target for fuzzable URLs|Honeypot Probabilty:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="striker-tool"', # tag if all regex match
    },
    'rhawk': {
        'name': 'rhawk',
        'regex1': r'S U B - D O M A I N   F I N D E R',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="rhawk-tool"', # tag if all regex match
    },
    'uniscan': {
        'name': 'uniscan',
        'regex1': r'\| \[\+\] E-mail Found:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="uniscan-tool"', # tag if all regex match
    },
    'masscan': {
        'name': 'masscan',
        'regex1': r'(?s)Starting masscan [\d.]+.+?Scanning|bit.ly/14GZzcT',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="masscan-tool"', # tag if all regex match
    },
    'msfconsole': {
        'name': 'msfconsole',
        'regex1': r'=\[ metasploit v[\d.]+.+?msf >',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="msfconsole-tool"', # tag if all regex match
    },
    'amap': {
        'name': 'amap',
        'regex1': r'\bamap v[\d.]+ \(www.thc.org/thc-amap\)',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="amap-tool"', # tag if all regex match
    },
    'automater': {
        'name': 'automater',
        'regex1': r'(?s)\[\*\] Checking.+?_+ Results found for:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="automater-tool"', # tag if all regex match
    },
    'braa': {
        'name': 'braa',
        'regex1': r'\bbraa public@[\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="braa-tool"', # tag if all regex match
    },
    'ciscotorch': {
        'name': 'ciscotorch',
        'regex1': r'Becase we need it',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="ciscotorch-tool"', # tag if all regex match
    },
    'theharvester': {
        'name': 'theharvester',
        'regex1': r'Starting harvesting process for domain:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="theharvester-tool"', # tag if all regex match
    },
    'sslstrip': {
        'name': 'sslstrip',
        'regex1': r'sslstrip [\d.]+ by Moxie Marlinspike running',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="sslstrip-tool"', # tag if all regex match
    },
    'sslcaudit': {
        'name': 'sslcaudit',
        'regex1': r'# filebag location:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="sslcaudit-tool"', # tag if all regex match
    },
    'smbmap': {
        'name': 'smbmap',
        'regex1': r'\[\+\] Finding open SMB ports\.\.\.',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="smbmap-tool"', # tag if all regex match
    },
    'reconng': {
        'name': 'reconng',
        'regex1': r'\[\*\] Status: unfixed|\[recon-ng\]\[default\]',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="reconng-tool"', # tag if all regex match
    },
    'p0f': {
        'name': 'p0f',
        'regex1': r'\bp0f [^ ]+ by Michal Zalewski',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="p0f-tool"', # tag if all regex match
    },
    'hping3': {
        'name': 'hping3',
        'regex1': r'\bHPING [^ ]+ \([^)]+\): [^ ]+ mode set',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="hping3-tool"', # tag if all regex match
    },
    'enum4linux': {
        'name': 'enum4linux',
        'regex1': r'Starting enum4linux v[\d.]+|\|    Target Information    \|',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="enum4linux-tool"', # tag if all regex match
    },
    'dnstracer': {
        'name': 'dnstracer',
        'regex1': r'(?s)Tracing to.+?DNS HEADER \(send\)',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dnstracer-tool"', # tag if all regex match
    },
    'dnmap': {
        'name': 'dnmap',
        'regex1': r'dnmap_(client|server)|Nmap output files stored in \'nmap_output\' directory',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dnmap-tool"', # tag if all regex match
    },
    'arpscan': {
        'name': 'arpscan',
        'regex1': r'Starting arp-scan [^ ]+ with \d+ hosts',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="arpscan-tool"', # tag if all regex match
    },
    'cdpsnarf': {
        'name': 'cdpsnarf',
        'regex1': r'(?s)CDPSnarf v[^ ]+.+?Waiting for a CDP packet\.\.\.',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="cdpsnarf-tool"', # tag if all regex match
    },
    'dnsmap': {
        'name': 'dnsmap',
        'regex1': r'DNS Network Mapper by pagvac',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dnsmap-tool"', # tag if all regex match
    },
    'dotdotpwn': {
        'name': 'dotdotpwn',
        'regex1': r'DotDotPwn v[^ ]+|dotdotpwn@sectester.net|\[\+\] Creating Traversal patterns',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dotdotpwn-tool"', # tag if all regex match
    },
    'searchsploit': {
        'name': 'searchsploit',
        'regex1': r'\| (exploits|shellcodes|)/|\.searchsploit_rc',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="searchsploit-tool"', # tag if all regex match
    },
    'fierce': {
        'name': 'fierce',
        'regex1': r'(?s)Trying zone transfer first.+Checking for wildcard DNS',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="fierce-tool"', # tag if all regex match
    },
    'firewalk': {
        'name': 'firewalk',
        'regex1': r'Firewalk state initialization completed successfully|Ramping phase source port',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="firewalk-tool"', # tag if all regex match
    },
    'fragroute': {
        'name': 'fragroute',
        'regex1': r'\bfragroute: tcp_seg -> ip_frag',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="fragroute-tool"', # tag if all regex match
    },
    'fragrouter': {
        'name': 'fragrouter',
        'regex1': r'fragrouter: frag-\d+:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="fragrouter-tool"', # tag if all regex match
    },
    'goofile': {
        'name': 'goofile',
        'regex1': r'code.google.com/p/goofile\b',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="goofile-tool"', # tag if all regex match
    },
    'intrace': {
        'name': 'intrace',
        'regex1': r'\bInTrace [\d.]+ \-\-',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="intrace-tool"', # tag if all regex match
    },
    'ismtp': {
        'name': 'ismtp',
        'regex1': r'Testing SMTP server \[user enumeration\]',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="ismtp-tool"', # tag if all regex match
    },
    'lbd': {
        'name': 'lbd',
        'regex1': r'Checking for (DNS|HTTP)-Loadbalancing',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="lbd-tool"', # tag if all regex match
    },
    'miranda': {
        'name': 'miranda',
        'regex1': r'Entering discovery mode for \'upnp:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="miranda-tool"', # tag if all regex match
    },
    'ncat': {
        'name': 'ncat',
        'regex1': r'nmap.org/ncat',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="ncat-tool"', # tag if all regex match
    },
    'ohrwurm': {
        'name': 'ohrwurm',
        'regex1': r'\bohrwurm-[\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="ohrwurm-tool"', # tag if all regex match
    },
    'oscanner': {
        'name': 'oscanner',
        'regex1': r'Loading services/sids from service file',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="oscanner-tool"', # tag if all regex match
    },
    'sfuzz': {
        'name': 'sfuzz',
        'regex1': r'AREALLYBADSTRING|sfuzz/sfuzz',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="sfuzz-tool"', # tag if all regex match
    },
    'sidguess': {
        'name': 'sidguess',
        'regex1': r'SIDGuesser v[\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="sidguess-tool"', # tag if all regex match
    },
    'sqlninja': {
        'name': 'sqlninja',
        'regex1': r'Sqlninja rel\. [\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="sqlninja-tool"', # tag if all regex match
    },
    'sqlsus': {
        'name': 'sqlsus',
        'regex1': r'sqlsus version [\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="sqlsus-tool"', # tag if all regex match
    },
    'dnsdict6': {
        'name': 'dnsdict6',
        'regex1': r'Starting DNS enumeration work on',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dnsdict6-tool"', # tag if all regex match
    },
    'unixprivesccheck': {
        'name': 'unixprivesccheck',
        'regex1': r'Recording Interface IP addresses',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="unixprivesccheck-tool"', # tag if all regex match
    },
    'yersinia': {
        'name': 'yersinia',
        'regex1': r'yersinia@yersinia.net',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="yersinia-tool"', # tag if all regex match
    },
    'armitage': {
        'name': 'armitage',
        'regex1': r'\[\*\] Starting msfrpcd for you',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="armitage-tool"', # tag if all regex match
    },
    'backdoorfactory': {
        'name': 'backdoorfactory',
        'regex1': r'\[\*\] In the backdoor module',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="backdoorfactory-tool"', # tag if all regex match
    },
    'beef': {
        'name': 'beef',
        'regex1': r'Please wait as BeEF services are started',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="beef-tool"', # tag if all regex match
    },
    'cat': {
        'name': 'cat',
        'regex1': r'Cisco Auditing Tool.+?g0ne',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="cat-tool"', # tag if all regex match
    },
    'cge': {
        'name': 'cge',
        'regex1': r'Vulnerability successful exploited with \[',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="cge-tool"', # tag if all regex match
    },
    'john': {
        'name': 'john',
        'regex1': r'John the Ripper password cracker, ver:|Loaded \d+ password hash \(',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="john-tool"', # tag if all regex match
    },
    'keimpx': {
        'name': 'keimpx',
        'regex1': r'\bkeimpx [\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="keimpx-tool"', # tag if all regex match
    },
    'maskprocessor': {
        'name': 'maskprocessor',
        'regex1': r'mp by atom, High-Performance word generator',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="maskprocessor-tool"', # tag if all regex match
    },
    'ncrack': {
        'name': 'ncrack',
        'regex1': r'Starting Ncrack[^\n]+http://ncrack.org',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="ncrack-tool"', # tag if all regex match
    },
    'patator': {
        'name': 'patator',
        'regex1': r'http://code.google.com/p/patator/|Starting Patator v',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="patator-tool"', # tag if all regex match
    },
    'phrasendrescher': {
        'name': 'phrasendrescher',
        'regex1': r'phrasen\|drescher [\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="phrasendrescher-tool"', # tag if all regex match
    },
    'polenum': {
        'name': 'polenum',
        'regex1': r'\[\+\] Password Complexity Flags:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="polenum-tool"', # tag if all regex match
    },
    'rainbowcrack': {
        'name': 'rainbowcrack',
        'regex1': r'Official Website: http://project-rainbowcrack.com/',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="rainbowcrack-tool"', # tag if all regex match
    },
    'rcracki_mt': {
        'name': 'rcracki_mt',
        'regex1': r'Found \d+ rainbowtable files\.\.\.',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="rcracki_mt-tool"', # tag if all regex match
    },
    'tcpdump': {
        'name': 'tcpdump',
        'regex1': r'tcpdump: listening on.+capture size \d+|\d+ packets received by filter',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="tcpdump-tool"', # tag if all regex match
    },
    'hydra': {
        'name': 'hydra',
        'regex1': r'Hydra \(http://www.thc.org/thc-hydra\)',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="hydra-tool"', # tag if all regex match
    },
    'netcat': {
        'name': 'netcat',
        'regex1': r'Listening on \[[\d.]+\] \(family',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="netcat-tool"', # tag if all regex match
    },
    'nslookup': {
        'name': 'nslookup',
        'regex1': r'Non-authoritative answer:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="nslookup-tool"', # tag if all regex match
    },
    'dig': {
        'name': 'dig',
        'regex1': r'; <<>> DiG [\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dig-tool"', # tag if all regex match
    },
    'whois': {
        'name': 'whois',
        'regex1': r'(?i)Registrar WHOIS Server:|Registrar URL: http://|DNSSEC: unsigned|information on Whois status codes|REGISTERED, DELEGATED|[Rr]egistrar:|%[^\n]+(WHOIS|2016/679)',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="whois-tool"', # tag if all regex match
    },
    'nessus': {
        'name': 'nessus',
        'regex1': r'nessus_(report_(get|list|exploits)|scan_(new|status))|nessuscli|nessusd|nessus-service',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="nessus-tool"', # tag if all regex match
    },
    'openvas': {
        'name': 'openvas',
        'regex1': r'/openvas/',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="openvas-tool"', # tag if all regex match
    },
    'golismero': {
        'name': 'golismero',
        'regex1': r'GoLismero[\n]+The Web Knife',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="golismero-tool"', # tag if all regex match
    },
    'wpscan': {
        'name': 'wpscan',
        'regex1': r'WordPress Security Scanner by the WPScan Team|\[\+\] Interesting header:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="wpscan-tool"', # tag if all regex match
    },
    'skipfish': {
        'name': 'skipfish',
        'regex1': r'\[\+\] Sorting and annotating crawl nodes:|skipfish version [\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="skipfish-tool"', # tag if all regex match
    },
    'arachni': {
        'name': 'arachni',
        'regex1': r'With the support of the community and the Arachni Team|\[\*\] Waiting for plugins to settle\.\.\.',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="arachni-tool"', # tag if all regex match
    },
    'dirb': {
        'name': 'dirb',
        'regex1': r'==> DIRECTORY:|\bDIRB v[\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dirb-tool"', # tag if all regex match
    },
    'joomscan': {
        'name': 'joomscan',
        'regex1': r'OWASP Joomla! Vulnerability Scanner v[\d.]+',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="joomscan-tool"', # tag if all regex match
    },
    'jbossautopwn': {
        'name': 'jbossautopwn',
        'regex1': r'\[x\] Now creating BSH script\.\.\.|\[x\] Now deploying \.war file:',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="jbossautopwn-tool"', # tag if all regex match
    },
    'grabber': {
        'name': 'grabber',
        'regex1': r'runSpiderScan @',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="grabber-tool"', # tag if all regex match
    },
    'fimap': {
        'name': 'fimap',
        'regex1': r'Automatic LFI/RFI scanner and exploiter',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="fimap-tool"', # tag if all regex match
    },
    'dsxs': {
        'name': 'dsxs',
        'regex1': r'Damn Small XSS Scanner \(DSXS\)',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dsxs-tool"', # tag if all regex match
    },
    'dsss': {
        'name': 'dsss',
        'regex1': r'Damn Small SQLi Scanner \(DSSS\)',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dsss-tool"', # tag if all regex match
    },
    'dsjs': {
        'name': 'dsjs',
        'regex1': r'Damn Small JS Scanner \(DSJS\)',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dsjs-tool"', # tag if all regex match
    },
    'dsfs': {
        'name': 'dsfs',
        'regex1': r'Damn Small FI Scanner \(DSFS\)',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="dsfs-tool"', # tag if all regex match
    },
    'identywaf': {
        'name': 'identywaf',
        'regex1': r'\[o\] initializing handlers\.\.\.',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="identywaf-tool"', # tag if all regex match
    },
    'whatwaf': {
        'name': 'whatwaf',
        'regex1': r'<sCRIPT>ALeRt.+?WhatWaf\?',
        'nb_regex': 1,
        'max_execution_time': default_max_execution_time,
        'tag': 'infoleak:automatic-detection="whatwaf-tool"', # tag if all regex match
    }
}

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Tools'
    # # TODO: add duplicate

    # Setup the I/O queues
    p = Process(config_section)

    # Sent to the logging a description of the module
    publisher.info("Run Tools module ")

    # Endless loop getting messages from the input queue
    while True:
        # Get one message from the input queue
        item_id = p.get_from_set()
        if item_id is None:
            publisher.debug("{} queue is empty, waiting".format(config_section))
            time.sleep(1)
            continue

        # Do something with the message from the queue
        item_content = Item.get_item_content(item_id)
        search_tools(item_id, item_content)

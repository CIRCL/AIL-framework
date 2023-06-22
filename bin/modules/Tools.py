#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Tools Module
============================

Search tools outpout

"""

import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects.Items import Item


TOOLS = {
    'sqlmap': {
        'regex': r'Usage of sqlmap for attacking targets without|all tested parameters do not appear to be injectable|sqlmap identified the following injection point|Title:[^\n]*((error|time|boolean)-based|stacked queries|UNION query)',
        'tag': 'infoleak:automatic-detection="sqlmap-tool"',
    },
    'wig': {
        'regex': r'(?s)wig - WebApp Information Gatherer.+?_{10,}',
        'tag': 'infoleak:automatic-detection="wig-tool"',
    },
    'dmytry': {
        'regex': r'(?s)Gathered (TCP Port|Inet-whois|Netcraft|Subdomain|E-Mail) information for.+?-{10,}',
        'tag': 'infoleak:automatic-detection="dmitry-tool"',
    },
    'inurlbr': {
        'regex': r'Usage of INURLBR for attacking targets without prior mutual consent is illegal',
        'tag': 'infoleak:automatic-detection="inurlbr-tool"',
    },
    'wafw00f': {
        'regex': r'(?s)WAFW00F - Web Application Firewall Detection Tool.+?Checking',
        'tag': 'infoleak:automatic-detection="wafw00f-tool"',
    },
    'sslyze': {
        'regex': r'(?s)PluginSessionRenegotiation.+?SCAN RESULTS FOR',
        'tag': 'infoleak:automatic-detection="sslyze-tool"',
    },
    'nmap': {
        'regex': r'(?s)Nmap scan report for.+?Host is',
        'tag': 'infoleak:automatic-detection="nmap-tool"',
    },
    'dnsenum': {
        'regex': r'(?s)dnsenum(\.pl)? VERSION:.+?Trying Zone Transfer',
        'tag': 'infoleak:automatic-detection="dnsenum-tool"',
    },
    'knock': {
        'regex': r'I scannig with my internal wordlist',
        'tag': 'infoleak:automatic-detection="knock-tool"',
    },
    'nikto': {
        'regex': r'(?s)\+ Target IP:.+?\+ Start Time:',
        'tag': 'infoleak:automatic-detection="nikto-tool"',
    },
    'dnscan': {
        'regex': r'(?s)\[\*\] Processing domain.+?\[\+\] Getting nameservers.+?records found',
        'tag': 'infoleak:automatic-detection="dnscan-tool"',
    },
    'dnsrecon': {
        'regex': r'Performing General Enumeration of Domain:|Performing TLD Brute force Enumeration against',
        'tag': 'infoleak:automatic-detection="dnsrecon-tool"',
    },
    'striker': {
        'regex': r'Crawling the target for fuzzable URLs|Honeypot Probabilty:',
        'tag': 'infoleak:automatic-detection="striker-tool"',
    },
    'rhawk': {
        'regex': r'S U B - D O M A I N   F I N D E R',
        'tag': 'infoleak:automatic-detection="rhawk-tool"',
    },
    'uniscan': {
        'regex': r'\| \[\+\] E-mail Found:',
        'tag': 'infoleak:automatic-detection="uniscan-tool"',
    },
    'masscan': {
        'regex': r'(?s)Starting masscan [\d.]+.+?Scanning|bit.ly/14GZzcT',
        'tag': 'infoleak:automatic-detection="masscan-tool"',
    },
    'msfconsole': {
        'regex': r'=\[ metasploit v[\d.]+.+?msf >',
        'tag': 'infoleak:automatic-detection="msfconsole-tool"',
    },
    'amap': {
        'regex': r'\bamap v[\d.]+ \(www.thc.org/thc-amap\)',
        'tag': 'infoleak:automatic-detection="amap-tool"',
    },
    'automater': {
        'regex': r'(?s)\[\*\] Checking.+?_+ Results found for:',
        'tag': 'infoleak:automatic-detection="automater-tool"',
    },
    'braa': {
        'regex': r'\bbraa public@[\d.]+',
        'tag': 'infoleak:automatic-detection="braa-tool"',
    },
    'ciscotorch': {
        'regex': r'Becase we need it',
        'tag': 'infoleak:automatic-detection="ciscotorch-tool"',
    },
    'theharvester': {
        'regex': r'Starting harvesting process for domain:',
        'tag': 'infoleak:automatic-detection="theharvester-tool"',
    },
    'sslstrip': {
        'regex': r'sslstrip [\d.]+ by Moxie Marlinspike running',
        'tag': 'infoleak:automatic-detection="sslstrip-tool"',
    },
    'sslcaudit': {
        'regex': r'# filebag location:',
        'tag': 'infoleak:automatic-detection="sslcaudit-tool"',
    },
    'smbmap': {
        'regex': r'\[\+\] Finding open SMB ports\.\.\.',
        'tag': 'infoleak:automatic-detection="smbmap-tool"',
    },
    'reconng': {
        'regex': r'\[\*\] Status: unfixed|\[recon-ng\]\[default\]',
        'tag': 'infoleak:automatic-detection="reconng-tool"',
    },
    'p0f': {
        'regex': r'\bp0f [^ ]+ by Michal Zalewski',
        'tag': 'infoleak:automatic-detection="p0f-tool"',
    },
    'hping3': {
        'regex': r'\bHPING [^ ]+ \([^)]+\): [^ ]+ mode set',
        'tag': 'infoleak:automatic-detection="hping3-tool"',
    },
    'enum4linux': {
        'regex': r'Starting enum4linux v[\d.]+|\|    Target Information    \|',
        'tag': 'infoleak:automatic-detection="enum4linux-tool"',
    },
    'dnstracer': {
        'regex': r'(?s)Tracing to.+?DNS HEADER \(send\)',
        'tag': 'infoleak:automatic-detection="dnstracer-tool"',
    },
    'dnmap': {
        'regex': r'dnmap_(client|server)|Nmap output files stored in \'nmap_output\' directory',
        'tag': 'infoleak:automatic-detection="dnmap-tool"',
    },
    'arpscan': {
        'regex': r'Starting arp-scan [^ ]+ with \d+ hosts',
        'tag': 'infoleak:automatic-detection="arpscan-tool"',
    },
    'cdpsnarf': {
        'regex': r'(?s)CDPSnarf v[^ ]+.+?Waiting for a CDP packet\.\.\.',
        'tag': 'infoleak:automatic-detection="cdpsnarf-tool"',
    },
    'dnsmap': {
        'regex': r'DNS Network Mapper by pagvac',
        'tag': 'infoleak:automatic-detection="dnsmap-tool"',
    },
    'dotdotpwn': {
        'regex': r'DotDotPwn v[^ ]+|dotdotpwn@sectester.net|\[\+\] Creating Traversal patterns',
        'tag': 'infoleak:automatic-detection="dotdotpwn-tool"',
    },
    'searchsploit': {
        'regex': r'(exploits|shellcodes)/|searchsploit_rc|Exploit Title',
        'tag': 'infoleak:automatic-detection="searchsploit-tool"',
    },
    'fierce': {
        'regex': r'(?s)Trying zone transfer first.+Checking for wildcard DNS',
        'tag': 'infoleak:automatic-detection="fierce-tool"',
    },
    'firewalk': {
        'regex': r'Firewalk state initialization completed successfully|Ramping phase source port',
        'tag': 'infoleak:automatic-detection="firewalk-tool"',
    },
    'fragroute': {
        'regex': r'\bfragroute: tcp_seg -> ip_frag',
        'tag': 'infoleak:automatic-detection="fragroute-tool"',
    },
    'fragrouter': {
        'regex': r'fragrouter: frag-\d+:',
        'tag': 'infoleak:automatic-detection="fragrouter-tool"',
    },
    'goofile': {
        'regex': r'code.google.com/p/goofile\b',
        'tag': 'infoleak:automatic-detection="goofile-tool"',
    },
    'intrace': {
        'regex': r'\bInTrace [\d.]+ \-\-',
        'tag': 'infoleak:automatic-detection="intrace-tool"',
    },
    'ismtp': {
        'regex': r'Testing SMTP server \[user enumeration\]',
        'tag': 'infoleak:automatic-detection="ismtp-tool"',
    },
    'lbd': {
        'regex': r'Checking for (DNS|HTTP)-Loadbalancing',
        'tag': 'infoleak:automatic-detection="lbd-tool"',
    },
    'miranda': {
        'regex': r'Entering discovery mode for \'upnp:',
        'tag': 'infoleak:automatic-detection="miranda-tool"',
    },
    'ncat': {
        'regex': r'nmap.org/ncat',
        'tag': 'infoleak:automatic-detection="ncat-tool"',
    },
    'ohrwurm': {
        'regex': r'\bohrwurm-[\d.]+',
        'tag': 'infoleak:automatic-detection="ohrwurm-tool"',
    },
    'oscanner': {
        'regex': r'Loading services/sids from service file',
        'tag': 'infoleak:automatic-detection="oscanner-tool"',
    },
    'sfuzz': {
        'regex': r'AREALLYBADSTRING|sfuzz/sfuzz',
        'tag': 'infoleak:automatic-detection="sfuzz-tool"',
    },
    'sidguess': {
        'regex': r'SIDGuesser v[\d.]+',
        'tag': 'infoleak:automatic-detection="sidguess-tool"',
    },
    'sqlninja': {
        'regex': r'Sqlninja rel\. [\d.]+',
        'tag': 'infoleak:automatic-detection="sqlninja-tool"',
    },
    'sqlsus': {
        'regex': r'sqlsus version [\d.]+',
        'tag': 'infoleak:automatic-detection="sqlsus-tool"',
    },
    'dnsdict6': {
        'regex': r'Starting DNS enumeration work on',
        'tag': 'infoleak:automatic-detection="dnsdict6-tool"',
    },
    'unixprivesccheck': {
        'regex': r'Recording Interface IP addresses',
        'tag': 'infoleak:automatic-detection="unixprivesccheck-tool"',
    },
    'yersinia': {
        'regex': r'yersinia@yersinia.net',
        'tag': 'infoleak:automatic-detection="yersinia-tool"',
    },
    'armitage': {
        'regex': r'\[\*\] Starting msfrpcd for you',
        'tag': 'infoleak:automatic-detection="armitage-tool"',
    },
    'backdoorfactory': {
        'regex': r'\[\*\] In the backdoor module',
        'tag': 'infoleak:automatic-detection="backdoorfactory-tool"',
    },
    'beef': {
        'regex': r'Please wait as BeEF services are started',
        'tag': 'infoleak:automatic-detection="beef-tool"',
    },
    'cat': {
        'regex': r'Cisco Auditing Tool.+?g0ne',
        'tag': 'infoleak:automatic-detection="cat-tool"',
    },
    'cge': {
        'regex': r'Vulnerability successful exploited with \[',
        'tag': 'infoleak:automatic-detection="cge-tool"',
    },
    'john': {
        'regex': r'John the Ripper password cracker, ver:|Loaded \d+ password hash \(',
        'tag': 'infoleak:automatic-detection="john-tool"',
    },
    'keimpx': {
        'regex': r'\bkeimpx [\d.]+',
        'tag': 'infoleak:automatic-detection="keimpx-tool"',
    },
    'maskprocessor': {
        'regex': r'mp by atom, High-Performance word generator',
        'tag': 'infoleak:automatic-detection="maskprocessor-tool"',
    },
    'ncrack': {
        'regex': r'Starting Ncrack[^\n]+http://ncrack.org',
        'tag': 'infoleak:automatic-detection="ncrack-tool"',
    },
    'patator': {
        'regex': r'http://code.google.com/p/patator/|Starting Patator v',
        'tag': 'infoleak:automatic-detection="patator-tool"',
    },
    'phrasendrescher': {
        'regex': r'phrasen\|drescher [\d.]+',
        'tag': 'infoleak:automatic-detection="phrasendrescher-tool"',
    },
    'polenum': {
        'regex': r'\[\+\] Password Complexity Flags:',
        'tag': 'infoleak:automatic-detection="polenum-tool"',
    },
    'rainbowcrack': {
        'regex': r'Official Website: http://project-rainbowcrack.com/',
        'tag': 'infoleak:automatic-detection="rainbowcrack-tool"',
    },
    'rcracki_mt': {
        'regex': r'Found \d+ rainbowtable files\.\.\.',
        'tag': 'infoleak:automatic-detection="rcracki_mt-tool"',
    },
    'tcpdump': {
        'regex': r'tcpdump: listening on.+capture size \d+|\d+ packets received by filter',
        'tag': 'infoleak:automatic-detection="tcpdump-tool"',
    },
    'hydra': {
        'regex': r'Hydra \(http://www.thc.org/thc-hydra\)',
        'tag': 'infoleak:automatic-detection="hydra-tool"',
    },
    'netcat': {
        'regex': r'Listening on \[[\d.]+\] \(family',
        'tag': 'infoleak:automatic-detection="netcat-tool"',
    },
    'nslookup': {
        'regex': r'Non-authoritative answer:',
        'tag': 'infoleak:automatic-detection="nslookup-tool"',
    },
    'dig': {
        'regex': r'; <<>> DiG [\d.]+',
        'tag': 'infoleak:automatic-detection="dig-tool"',
    },
    'whois': {
        'regex': r'(?i)Registrar WHOIS Server:|Registrar URL: http://|DNSSEC: unsigned|information on Whois status codes|REGISTERED, DELEGATED|[Rr]egistrar:|%[^\n]+(WHOIS|2016/679)',
        'tag': 'infoleak:automatic-detection="whois-tool"',
    },
    'nessus': {
        'regex': r'nessus_(report_(get|list|exploits)|scan_(new|status))|nessuscli|nessusd|nessus-service',
        'tag': 'infoleak:automatic-detection="nessus-tool"',
    },
    'openvas': {
        'regex': r'/openvas/',
        'tag': 'infoleak:automatic-detection="openvas-tool"',
    },
    'golismero': {
        'regex': r'GoLismero[\n]+The Web Knife',
        'tag': 'infoleak:automatic-detection="golismero-tool"',
    },
    'wpscan': {
        'regex': r'WordPress Security Scanner by the WPScan Team|\[\+\] Interesting header:',
        'tag': 'infoleak:automatic-detection="wpscan-tool"',
    },
    'skipfish': {
        'regex': r'\[\+\] Sorting and annotating crawl nodes:|skipfish version [\d.]+',
        'tag': 'infoleak:automatic-detection="skipfish-tool"',
    },
    'arachni': {
        'regex': r'With the support of the community and the Arachni Team|\[\*\] Waiting for plugins to settle\.\.\.',
        'tag': 'infoleak:automatic-detection="arachni-tool"',
    },
    'dirb': {
        'regex': r'==> DIRECTORY:|\bDIRB v[\d.]+',
        'tag': 'infoleak:automatic-detection="dirb-tool"',
    },
    'joomscan': {
        'regex': r'OWASP Joomla! Vulnerability Scanner v[\d.]+',
        'tag': 'infoleak:automatic-detection="joomscan-tool"',
    },
    'jbossautopwn': {
        'regex': r'\[x\] Now creating BSH script\.\.\.|\[x\] Now deploying \.war file:',
        'tag': 'infoleak:automatic-detection="jbossautopwn-tool"',
    },
    'grabber': {
        'regex': r'runSpiderScan @',
        'tag': 'infoleak:automatic-detection="grabber-tool"',
    },
    'fimap': {
        'regex': r'Automatic LFI/RFI scanner and exploiter',
        'tag': 'infoleak:automatic-detection="fimap-tool"',
    },
    'dsxs': {
        'regex': r'Damn Small XSS Scanner \(DSXS\)',
        'tag': 'infoleak:automatic-detection="dsxs-tool"',
    },
    'dsss': {
        'regex': r'Damn Small SQLi Scanner \(DSSS\)',
        'tag': 'infoleak:automatic-detection="dsss-tool"',
    },
    'dsjs': {
        'regex': r'Damn Small JS Scanner \(DSJS\)',
        'tag': 'infoleak:automatic-detection="dsjs-tool"',
    },
    'dsfs': {
        'regex': r'Damn Small FI Scanner \(DSFS\)',
        'tag': 'infoleak:automatic-detection="dsfs-tool"',
    },
    'identywaf': {
        'regex': r'\[o\] initializing handlers\.\.\.',
        'tag': 'infoleak:automatic-detection="identywaf-tool"',
    },
    'whatwaf': {
        'regex': r'<sCRIPT>ALeRt.+?WhatWaf\?',
        'tag': 'infoleak:automatic-detection="whatwaf-tool"',
    }
}

class Tools(AbstractModule):
    """
    Tools module for AIL framework
    """

    def __init__(self, queue=True):
        super(Tools, self).__init__(queue=queue)

        self.max_execution_time = 30
        # Waiting time in seconds between to message processed
        self.pending_seconds = 10
        # Send module state to logs
        self.logger.info(f"Module {self.module_name} initialized")

    def get_tools(self):
        return TOOLS.keys()

    def extract(self, obj_id, content, tag):
        extracted = []
        tool_name = tag.rsplit('"', 2)[1][:-5]
        tools = self.regex_finditer(TOOLS[tool_name]['regex'], obj_id, content)
        for tool in tools:
            extracted.append([tool[0], tool[1], tool[2], f'tag:{tag}'])
        return extracted

    def compute(self, message):
        item = self.get_obj()
        content = item.get_content()

        for tool_name in TOOLS:
            tool = TOOLS[tool_name]
            match = self.regex_search(tool['regex'], item.id, content)
            if match:
                print(f'{item.id} found: {tool_name}')
                # Tag Item
                tag = tool['tag']
                self.add_message_to_queue(message=tag, queue='Tags')
                # TODO ADD LOGS


if __name__ == '__main__':
    module = Tools()
    module.run()


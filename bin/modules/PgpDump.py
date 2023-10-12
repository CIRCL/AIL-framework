#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
The PgpDump Module
======================

This module Extract ID from PGP Blocks.

"""

##################################
# Import External packages
##################################
import os
import sys
import subprocess

from bs4 import BeautifulSoup
from uuid import uuid4

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from modules.abstract_module import AbstractModule
from lib.objects import Pgps
from trackers.Tracker_Term import Tracker_Term
from trackers.Tracker_Regex import Tracker_Regex
from trackers.Tracker_Yara import Tracker_Yara


class PgpDump(AbstractModule):
    """
    Cve module for AIL framework
    """

    def __init__(self):
        super(PgpDump, self).__init__()

        # check/create pgpdump queue directory (used for huge pgp blocks)
        self.pgpdump_dir = os.path.join(os.environ['AIL_HOME'], 'temp', 'pgpdump')
        if not os.path.isdir(self.pgpdump_dir):
            os.makedirs(self.pgpdump_dir)

        # Regex
        self.reg_user_id = r'User ID - .+'
        self.reg_key_id = r'Key ID - .+'
        self.reg_pgp_public_blocs = r'-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]+?-----END PGP PUBLIC KEY BLOCK-----'
        self.reg_pgp_private_blocs = r'-----BEGIN PGP PRIVATE KEY BLOCK-----[\s\S]+?-----END PGP PRIVATE KEY BLOCK-----'
        self.reg_pgp_signature = r'-----BEGIN PGP SIGNATURE-----[\s\S]+?-----END PGP SIGNATURE-----'
        self.reg_pgp_message = r'-----BEGIN PGP MESSAGE-----[\s\S]+?-----END PGP MESSAGE-----'
        self.reg_tool_version = r'\bVersion:.*\n'
        self.reg_block_comment = r'\bComment:.*\n'

        # Waiting time in seconds between to message processed
        self.pending_seconds = 1

        self.tracker_term = Tracker_Term(queue=False)
        self.tracker_regex = Tracker_Regex(queue=False)
        self.tracker_yara = Tracker_Yara(queue=False)

        # init
        self.keys = set()
        self.private_keys = set()
        self.names = set()
        self.mails = set()
        self.symmetrically_encrypted = False

        # Send module state to logs
        self.logger.info(f'Module {self.module_name} initialized')

    def remove_html(self, pgp_block):
        try:
            if bool(BeautifulSoup(pgp_block, "html.parser").find()):
                soup = BeautifulSoup(pgp_block, 'html.parser')
                # kill all script and style elements
                for script in soup(["script", "style"]):
                    script.extract()  # remove

                # get text
                text = soup.get_text()
                return text
            else:
                return pgp_block
        except TypeError:
            return pgp_block

    def sanitize_pgp_block(self, pgp_block):
        # Debug
        print(pgp_block)
        print()
        pgp_block = self.remove_html(pgp_block)
        # Remove Version
        versions = self.regex_findall(self.reg_tool_version, self.obj.id, pgp_block)
        for version in versions:
            pgp_block = pgp_block.replace(version, '')
        # Remove Comment
        comments = self.regex_findall(self.reg_block_comment, self.obj.id, pgp_block)
        for comment in comments:
            pgp_block = pgp_block.replace(comment, '')
        # Remove Empty Lines
        pgp_block = [s for s in pgp_block.splitlines() if (s and not s.isspace())]
        pgp_block[0] = pgp_block[0] + '\n'
        pgp_block[-1] = '\n' + pgp_block[-1]
        pgp_block = '\n'.join(pgp_block)

        # Debug
        print(pgp_block)
        print('-------------------------------------------------------------------------')
        return pgp_block

    def get_pgpdump_from_file(self, pgp_block):
        print('Save PGP Block in File')
        file_uuid = str(uuid4())
        filepath = os.path.join(self.pgpdump_dir, file_uuid)
        with open(filepath, 'w') as f:
            f.write(pgp_block)
        process1 = subprocess.Popen(['pgpdump', filepath], stdout=subprocess.PIPE)
        output = process1.communicate()[0].decode()
        os.remove(filepath)
        return output

    def get_pgpdump_from_terminal(self, pgp_block):
        process1 = subprocess.Popen(['echo', '-e', pgp_block], stdout=subprocess.PIPE)
        process2 = subprocess.Popen(['pgpdump'], stdin=process1.stdout, stdout=subprocess.PIPE)
        process1.stdout.close()
        output = process2.communicate()[0]
        try:
            output = output.decode()
        except UnicodeDecodeError:
            self.logger.error(f'Error PgpDump UnicodeDecodeError: {self.obj.id}')
            output = ''
        return output

    def get_pgpdump(self, pgp_block):
        if len(pgp_block) > 131072:
            return self.get_pgpdump_from_file(pgp_block)
        else:
            return self.get_pgpdump_from_terminal(pgp_block)

    def extract_id_from_pgpdump_output(self, pgpdump_output):
        if 'Secret Key Packet' in pgpdump_output:
            private = True
        else:
            private = False
        users = self.regex_findall(self.reg_user_id, self.obj.id, pgpdump_output)
        for user in users:
            # avoid key injection in user_id:
            pgpdump_output.replace(user, '', 1)
            user = user.replace('User ID - ', '', 1)
            if ' <' in user:
                name, mail = user.rsplit(' <', 1)
                mail = mail[:-1]
                self.names.add(name)
                self.mails.add(mail)
            else:
                name = user
                self.names.add(name)

        keys = self.regex_findall(self.reg_key_id, self.obj.id, pgpdump_output)
        for key_id in keys:
            key_id = key_id.replace('Key ID - ', '', 1)
            if key_id != '0x0000000000000000':
                self.keys.add(key_id)
                if private:
                    self.private_keys.add(key_id)
            else:
                self.symmetrically_encrypted = True
                print('symmetrically encrypted')

    def compute(self, message):
        content = self.obj.get_content()

        pgp_blocks = []
        # Public Block
        for pgp_block in self.regex_findall(self.reg_pgp_public_blocs, self.obj.id, content):
            # content = content.replace(pgp_block, '')
            pgp_block = self.sanitize_pgp_block(pgp_block)
            pgp_blocks.append(pgp_block)
        # Private Block
        for pgp_block in self.regex_findall(self.reg_pgp_private_blocs, self.obj.id, content):
            # content = content.replace(pgp_block, '')
            pgp_block = self.sanitize_pgp_block(pgp_block)
            pgp_blocks.append(pgp_block)
        # Signature
        for pgp_block in self.regex_findall(self.reg_pgp_signature, self.obj.id, content):
            # content = content.replace(pgp_block, '')
            pgp_block = self.sanitize_pgp_block(pgp_block)
            pgp_blocks.append(pgp_block)
        # Message
        for pgp_block in self.regex_findall(self.reg_pgp_message, self.obj.id, content):
            pgp_block = self.sanitize_pgp_block(pgp_block)
            pgp_blocks.append(pgp_block)

        self.symmetrically_encrypted = False
        self.keys = set()
        self.private_keys = set()
        self.names = set()
        self.mails = set()
        for pgp_block in pgp_blocks:
            pgpdump_output = self.get_pgpdump(pgp_block)
            self.extract_id_from_pgpdump_output(pgpdump_output)

        if self.keys or self.names or self.mails:
            print(self.obj.id)
            date = self.obj.get_date()
            for key in self.keys:
                pgp = Pgps.Pgp(key, 'key')
                pgp.add(date, self.obj)
                print(f'    key: {key}')
            for name in self.names:
                pgp = Pgps.Pgp(name, 'name')
                pgp.add(date, self.obj)
                print(f'    name: {name}')
                self.tracker_term.compute_manual(pgp)
                self.tracker_regex.compute_manual(pgp)
                self.tracker_yara.compute_manual(pgp)
            for mail in self.mails:
                pgp = Pgps.Pgp(mail, 'mail')
                pgp.add(date, self.obj)
                print(f'    mail: {mail}')
                self.tracker_term.compute_manual(pgp)
                self.tracker_regex.compute_manual(pgp)
                self.tracker_yara.compute_manual(pgp)

            # Keys extracted from PGP PRIVATE KEY BLOCK
            for key in self.private_keys:
                pgp = Pgps.Pgp(key, 'key')
                pgp.add_tag('infoleak:automatic-detection="pgp-private-key"')
                print(f'    private key: {key}')

        if self.symmetrically_encrypted:
            tag = 'infoleak:automatic-detection="pgp-symmetric"'
            self.add_message_to_queue(message=tag, queue='Tags')


if __name__ == '__main__':
    module = PgpDump()
    module.run()

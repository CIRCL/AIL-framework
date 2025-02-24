#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import os
import logging
import logging.config
import sys

from abc import ABC
from ssl import create_default_context

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# from flask import escape

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_logger
from lib import ail_users
from exporter.abstract_exporter import AbstractExporter
from lib.ConfigLoader import ConfigLoader
# from lib.objects.abstract_object import AbstractObject
# from lib.Tracker import Tracker

logging.config.dictConfig(ail_logger.get_config(name='modules'))


class MailExporter(AbstractExporter, ABC):
    def __init__(self, host=None, port=None, password=None, user='', sender='', cert_required=None, ca_file=None):
        super().__init__()
        config_loader = ConfigLoader()

        self.logger = logging.getLogger(f'{self.__class__.__name__}')

        if host:
            self.host = host
            self.port = port
        else:
            self.host = config_loader.get_config_str("Notifications", "sender_host")
            self.port = config_loader.get_config_int("Notifications", "sender_port")
        if password:
            self.pw = password
        else:
            self.pw = config_loader.get_config_str("Notifications", "sender_pw")
            if self.pw == 'None':
                self.pw = None
        if cert_required is not None:
            self.cert_required = bool(cert_required)
            self.ca_file = ca_file
        else:
            self.cert_required = config_loader.get_config_boolean("Notifications", "cert_required")
            if self.cert_required:
                self.ca_file = config_loader.get_config_str("Notifications", "ca_file")
            else:
                self.ca_file = None
        if user:
            self.user = user
        else:
            self.user = config_loader.get_config_str("Notifications", "sender_user")
        if sender:
            self.sender = sender
        else:
            self.sender = config_loader.get_config_str("Notifications", "sender")

        # raise an exception if any of these is None
        if (self.sender is None or
                self.host is None or
                self.port is None):
            raise Exception('SMTP configuration (host, port, sender) is missing or incomplete!')

    def get_smtp_client(self):
        # try:
        smtp_server = smtplib.SMTP(self.host, self.port)
        if self.pw is not None:
            try:
                smtp_server.ehlo()
                smtp_server.starttls()
            except smtplib.SMTPNotSupportedError:
                self.logger.info(f"The server {self.host}:{self.port} does not support the STARTTLS extension.")
                if self.cert_required:
                    context = create_default_context(cafile=self.ca_file)
                else:
                    context = None
                smtp_server = smtplib.SMTP_SSL(self.host, self.port, context=context)

            smtp_server.ehlo()
            if self.user is not None:
                smtp_server.login(self.user, self.pw)
            else:
                smtp_server.login(self.sender, self.pw)
        return smtp_server
        # except Exception as err:
        # traceback.print_tb(err.__traceback__)
        # self.logger.warning(err)

    def _export(self, recipient, subject, body):
        mime_msg = MIMEMultipart()
        mime_msg['From'] = self.sender
        mime_msg['To'] = recipient
        mime_msg['Subject'] = subject
        mime_msg.attach(MIMEText(body, 'plain'))

        # try:
        smtp_client = self.get_smtp_client()
        smtp_client.sendmail(self.sender, recipient, mime_msg.as_string())
        smtp_client.quit()
        # except Exception as err:
        # traceback.print_tb(err.__traceback__)
        # self.logger.warning(err)
        self.logger.info(f'Send notification: {subject} to {recipient}')

class MailExporterTracker(MailExporter):

    def __init__(self, host=None, port=None, password=None, user='', sender=''):
        super().__init__(host=host, port=port, password=password, user=user, sender=sender)

    def export(self, tracker, obj, matches=[]):
        tracker_type = tracker.get_type()
        tracker_name = tracker.get_tracked()
        description = tracker.get_description()
        if not description:
            description = tracker_name

        subject = f'AIL Framework Tracker: {description}'
        body = f"AIL Framework, New occurrence for {tracker_type} tracker: {tracker_name}\n"
        body += f'Object {obj.type}: {obj.id}\n'

        if matches:
            body += '\n'
            nb = 1
            for match in matches:
                body += f'\nMatch {nb}: {match[0]}\nExtract:\n{match[1]}\n\n'
                nb += 1

        ail_link = f'AIL url:{obj.get_link()}\n\n'
        for mail in tracker.get_mails():
            if ail_users.exists_user(mail):
                body = ail_link + body
            self._export(mail, subject, body)

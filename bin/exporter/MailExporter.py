#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Importer Class
================

Import Content

"""
import os
import sys

from abc import ABC

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# from flask import escape

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from exporter.abstract_exporter import AbstractExporter
from lib.ConfigLoader import ConfigLoader
# from lib.objects.abstract_object import AbstractObject
# from lib.Tracker import Tracker


class MailExporter(AbstractExporter, ABC):
    def __init__(self, host=None, port=None, password=None, user='', sender=''):
        super().__init__()
        config_loader = ConfigLoader()

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
        if self.pw is not None:
            try:
                smtp_server = smtplib.SMTP(self.host, self.port)
                smtp_server.starttls()
            except smtplib.SMTPNotSupportedError:
                print("The server does not support the STARTTLS extension.")
                smtp_server = smtplib.SMTP_SSL(self.host, self.port)

            smtp_server.ehlo()
            if self.user is not None:
                smtp_server.login(self.user, self.pw)
            else:
                smtp_server.login(self.sender, self.pw)
        else:
            smtp_server = smtplib.SMTP(self.host, self.port)
        return smtp_server
        # except Exception as err:
        # traceback.print_tb(err.__traceback__)
        # logger.warning(err)

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
        # logger.warning(err)
        print(f'Send notification: {subject} to {recipient}')

class MailExporterTracker(MailExporter):

    def __init__(self, host=None, port=None, password=None, user='', sender=''):
        super().__init__(host=host, port=port, password=password, user=user, sender=sender)

    def export(self, tracker, obj):  # TODO match
        tracker_type = tracker.get_type()
        tracker_name = tracker.get_tracked()
        subject = f'AIL Framework Tracker: {tracker_name}'  # TODO custom subject
        body = f"AIL Framework, New occurrence for {tracker_type} tracker: {tracker_name}\n"
        body += f'Item: {obj.id}\nurl:{obj.get_link()}'

        # TODO match option
        # if match:
        #     body += f'Tracker Match:\n\n{escape(match)}'

        for mail in tracker.get_mails():
            self._export(mail, subject, body)

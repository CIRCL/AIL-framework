#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

import argparse
import traceback
import smtplib
from pubsublogger import publisher
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

"""
This module allows the global configuration and management of notification settings and methods.
"""

config_loader = ConfigLoader.ConfigLoader()

publisher.port = 6380
publisher.channel = "Script"

def sendEmailNotification(recipient, alert_name, content):

    sender = config_loader.get_config_str("Notifications", "sender")
    sender_user = config_loader.get_config_str("Notifications", "sender_user")
    sender_host = config_loader.get_config_str("Notifications", "sender_host")
    sender_port = config_loader.get_config_int("Notifications", "sender_port")
    sender_pw = config_loader.get_config_str("Notifications", "sender_pw")
    if sender_pw == 'None':
        sender_pw = None

    # raise an exception if any of these is None
    if (sender is None or
        sender_host is None or
        sender_port is None
        ):
        raise Exception('SMTP configuration (host, port, sender) is missing or incomplete!')

    try:
        if sender_pw is not None:
            try:
                smtp_server = smtplib.SMTP(sender_host, sender_port)
                smtp_server.starttls()
            except smtplib.SMTPNotSupportedError:
                print("The server does not support the STARTTLS extension.")
                smtp_server = smtplib.SMTP_SSL(sender_host, sender_port)

            smtp_server.ehlo()
            if sender_user is not None:
                smtp_server.login(sender_user, sender_pw)
            else:
                smtp_server.login(sender, sender_pw)
        else:
            smtp_server = smtplib.SMTP(sender_host, sender_port)

        mime_msg = MIMEMultipart()
        mime_msg['From'] = sender
        mime_msg['To'] = recipient
        mime_msg['Subject'] = "AIL Framework " + alert_name + " Alert"

        body = content
        mime_msg.attach(MIMEText(body, 'plain'))

        smtp_server.sendmail(sender, recipient, mime_msg.as_string())
        smtp_server.quit()
        print('Send notification ' + alert_name + ' to '+recipient)

    except Exception as err:
        traceback.print_tb(err.__traceback__)
        publisher.warning(err)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test notification sender.')
    parser.add_argument("addr", help="Test mail 'to' address")
    args = parser.parse_args()
    sendEmailNotification(args.addr, '_mail test_', 'Success.')

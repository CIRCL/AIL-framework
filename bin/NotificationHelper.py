#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import argparse
import configparser
import traceback
import os
import smtplib
from pubsublogger import publisher
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

"""
This module allows the global configuration and management of notification settings and methods.
"""

# CONFIG #
configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')

publisher.port = 6380
publisher.channel = "Script"

# notifications enabled/disabled
TrackedTermsNotificationEnabled_Name = "TrackedNotifications"

# associated notification email addresses for a specific term`
# Keys will be e.g. TrackedNotificationEmails<TERMNAME>
TrackedTermsNotificationEmailsPrefix_Name = "TrackedNotificationEmails_"

def sendEmailNotification(recipient, alert_name, content):

    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                    Did you set environment variables? \
                    Or activate the virtualenv?')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    sender = cfg.get("Notifications", "sender")
    sender_host = cfg.get("Notifications", "sender_host")
    sender_port = cfg.getint("Notifications", "sender_port")
    sender_pw = cfg.get("Notifications", "sender_pw")
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

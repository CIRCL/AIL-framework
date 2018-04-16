#!/usr/bin/env python3.5
# -*-coding:UTF-8 -*

import configparser
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

"""
This module allows the global configuration and management of notification settings and methods.
"""

# CONFIG #
configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')

# notifications enabled/disabled
TrackedTermsNotificationEnabled_Name = "TrackedNotifications"

# associated notification email addresses for a specific term`
# Keys will be e.g. TrackedNotificationEmails<TERMNAME>
TrackedTermsNotificationEmailsPrefix_Name = "TrackedNotificationEmails_"

def sendEmailNotification(recipient, term):

    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                    Did you set environment variables? \
                    Or activate the virtualenv?')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    sender = cfg.get("Notifications", "sender"),
    sender_host = cfg.get("Notifications", "sender_host"),
    sender_port = cfg.getint("Notifications", "sender_port"),
    sender_pw = cfg.get("Notifications", "sender_pw"),

    if isinstance(sender, tuple):
        sender = sender[0]

    if isinstance(sender_host, tuple):
        sender_host = sender_host[0]

    if isinstance(sender_port, tuple):
        sender_port = sender_port[0]

    if isinstance(sender_pw, tuple):
        sender_pw = sender_pw[0]

    # raise an exception if any of these is None
    if (sender is None or
        sender_host is None or
        sender_port is None
        ):
        raise Exception('SMTP configuration (host, port, sender) is missing or incomplete!')

    try:
        if sender_pw is not None:
            smtp_server = smtplib.SMTP_SSL(sender_host, sender_port)
            smtp_server.ehlo()
            smtp_server.login(sender, sender_pw)
        else:
            smtp_server = smtplib.SMTP(sender_host, sender_port)


        mime_msg = MIMEMultipart()
        mime_msg['From'] = sender
        mime_msg['To'] = recipient
        mime_msg['Subject'] = "AIL Term Alert"

        body = "New occurrence for term: " + term
        mime_msg.attach(MIMEText(body, 'plain'))

        smtp_server.sendmail(sender, recipient, mime_msg.as_string())
        smtp_server.quit()

    except Exception as e:
        print(str(e))
        # raise e

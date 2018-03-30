#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import ConfigParser
import os
import smtplib
from email.MIMEMultipart import MIMEMultipart
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

    cfg = ConfigParser.ConfigParser()
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
            
    if (
        sender is not None and
        sender_host is not None and
        sender_port is not None and
        sender_pw is not None
       ):
        try:                    
                                  
            server_ssl = smtplib.SMTP_SSL(sender_host, sender_port)
            server_ssl.ehlo()
            server_ssl.login(sender, sender_pw)
            
            mime_msg = MIMEMultipart()
            mime_msg['From'] = sender
            mime_msg['To'] = recipient
            mime_msg['Subject'] = "AIL Term Alert"
            
            body = "New occurrence for term: " + term
            mime_msg.attach(MIMEText(body, 'plain'))
            
            server_ssl.sendmail(sender, recipient, mime_msg.as_string())
            server_ssl.quit()
            
        except Exception as e:
            print str(e)
            # raise e
    elif (
            sender is not None and
            sender_host is not None and
            sender_port is not None
        ):
        try:

            server = smtplib.SMTP(sender_host, sender_port)

            mime_msg = MIMEMultipart()
            mime_msg['From'] = sender
            mime_msg['To'] = recipient
            mime_msg['Subject'] = "AIL Term Alert"
            
            body = "New occurrence for term: " + term
            mime_msg.attach(MIMEText(body, 'plain'))
            
            server.sendmail(sender, recipient, mime_msg.as_string())
            server.quit()

        except Exception as e:
            print str(e)
            # raise e



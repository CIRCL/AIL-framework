#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
Yara trackers

"""
import os
import re
import sys
import time
import yara

from pubsublogger import publisher

sys.path.append(os.environ['AIL_BIN'])
from Helper import Process
import NotificationHelper # # TODO: refractor

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages'))
import Term

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import Tracker
import item_basic


full_item_url = "/object/item?id="
mail_body_template = "AIL Framework,\nNew YARA match: {}\nitem id: {}\nurl: {}{}"

last_refresh = time.time()

def yara_rules_match(data):
    #print(data)
    tracker_uuid = data['namespace']

    item_date = item_basic.get_item_date(item_id)
    Tracker.add_tracked_item(tracker_uuid, item_id, item_date)

    # Tags
    tags_to_add = Tracker.get_tracker_tags(tracker_uuid)
    for tag in tags_to_add:
        msg = '{};{}'.format(tag, item_id)
        p.populate_set_out(msg, 'Tags')

    # Mails
    mail_to_notify = Tracker.get_tracker_mails(tracker_uuid)
    if mail_to_notify:
        mail_subject = Tracker.get_email_subject(tracker_uuid)
        mail_body = mail_body_template.format(data['rule'], item_id, full_item_url, item_id)
    for mail in mail_to_notify:
        NotificationHelper.sendEmailNotification(mail, mail_subject, mail_body)

    return yara.CALLBACK_CONTINUE

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"
    publisher.info("Script Tracker_Yara started")

    config_section = 'Tracker_Yara'
    module_name = "Tracker_Yara"
    p = Process(config_section)

    full_item_url = p.config.get("Notifications", "ail_domain") + full_item_url

    # Load Yara rules
    rules = Tracker.reload_yara_rules()

    # Regex Frequency
    while True:
        item_id = p.get_from_set()
        if item_id is not None:
            item_content = item_basic.get_item_content(item_id)
            yara_match = rules.match(data=item_content, callback=yara_rules_match, which_callbacks=yara.CALLBACK_MATCHES, timeout=60)
            if yara_match:
                print(f'{item_id}: {yara_match}')

        else:
            time.sleep(5)

        # refresh YARA list
        if last_refresh < Tracker.get_tracker_last_updated_by_type('yara'):
            rules = Tracker.reload_yara_rules()
            last_refresh = time.time()
            print('Tracked set refreshed')

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

default_subject = 'AIL services credentials'

def get_default_template(user_id, password):
    return f'''Dear AIL user,

Here are your credentials to access the AIL services.

Afterward, you can use the following credentials and setup for your MFA:

Login: {user_id}
Password: {password}

We hope this information is helpful.

Best regards,'''

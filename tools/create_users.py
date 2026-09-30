#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import argparse
import sys

from pyail import PyAIL

AIL_URL = 'https://localhost:7000'
AIL_KEY = ''
org_uuid = ''


def get_ail():
    return PyAIL(AIL_URL, AIL_KEY, ssl=True)

def create_users(users_file):
    ail = get_ail()
    with open(users_file, 'r') as f:
        for line in f:
            line = line.strip()
            user_id = line.lower()
            r = ail.create_user(org_uuid, user_id, 'user', send_email=True)
            print(r)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create list of users')
    parser.add_argument('-f', '--file', type=str, help='file of line by line users', required=True)

    args = parser.parse_args()
    if not args.file:
        parser.print_help()
        sys.exit(0)

    create_users(args.file)

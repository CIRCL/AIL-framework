#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
Update AIL
============================

Update AIL clone and fork

"""

import configparser
import os
import sys
import argparse

import subprocess

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
# TODO: move other functions
from packages import git_status


UPDATER_FILENAME = os.path.join(os.environ['AIL_BIN'], 'Update.py')

UPDATER_LAST_MODIFICATION = float(os.stat(UPDATER_FILENAME).st_mtime)

def auto_update_enabled(cfg):
    auto_update = cfg.get('Update', 'auto_update')
    if auto_update == 'True' or auto_update == 'true':
        return True
    else:
        return False

def update_submodule():
    print(f'{TERMINAL_YELLOW}git submodule update:{TERMINAL_DEFAULT}')
    process = subprocess.run(['git', 'submodule', 'update'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        res = process.stdout.decode()
        print(res)
        print(f'{TERMINAL_YELLOW}Submodules Updated{TERMINAL_DEFAULT}')
        print()
    else:
        print('Error updating submodules:')
        print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
        print()


# check if files are modify locally
def check_if_files_modified():
    # return True
    process = subprocess.run(['git', 'ls-files', '-m'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        modified_files = process.stdout
        if modified_files:
            l_modified_files = []
            for modified_file in modified_files.decode().split('\n'):
                if modified_file:
                    if modified_file.split('/')[0] != 'configs':
                        l_modified_files.append(modified_file)
            if l_modified_files:
                print('Modified Files:')
                for modified_file in l_modified_files:
                    print(f'{TERMINAL_BLUE}{modified_file}{TERMINAL_DEFAULT}')
                print()
                return False
            else:
                return True
        else:
            return True
    else:
        print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
        sys.exit(1)

def repo_is_fork():
    # return False
    print('Check if this repository is a fork:')
    process = subprocess.run(['git', 'remote', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode == 0:
        res = process.stdout.decode()
        if f'origin	{AIL_REPO}' in res or f'origin	git@github.com:{AIL_REPO_NAME}' in res:
            print(f'    This repository is a {TERMINAL_BLUE}clone of {AIL_REPO}{TERMINAL_DEFAULT}')
            return False
        elif f'origin	{OLD_AIL_REPO}' in res:
            print('    old AIL repository, Updating remote origin...')
            res = git_status.set_default_remote(AIL_REPO, verbose=False)
            if res:
                return False
            else:
                return True
        else:
            print(f'    This repository is a {TERMINAL_BLUE}fork{TERMINAL_DEFAULT}')
            print()
            return True
    else:
        print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
        aborting_update()
        sys.exit(0)

def is_upstream_created(upstream):
    process = subprocess.run(['git', 'remote', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        output = process.stdout.decode()
        if upstream in output:
            return True
        else:
            return False
    else:
        print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
        aborting_update()
        sys.exit(0)

def create_fork_upstream(upstream):
    print(f'{TERMINAL_YELLOW}... Creating upstream ...{TERMINAL_DEFAULT}')
    print(f'git remote add {upstream} {AIL_REPO}')
    process = subprocess.run(['git', 'remote', 'add', upstream, AIL_REPO],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        print(process.stdout.decode())
        if is_upstream_created(upstream):
            print('Fork upstream created')
            print(f'{TERMINAL_YELLOW}...    ...{TERMINAL_DEFAULT}')
        else:
            print('Fork not created')
            aborting_update()
            sys.exit(0)
    else:
        print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
        aborting_update()
        sys.exit(0)

def update_fork():
    print(f'{TERMINAL_YELLOW}... Updating fork ...{TERMINAL_DEFAULT}')
    if cfg.get('Update', 'update-fork') == 'True' or cfg.get('Update', 'update-fork') == 'true':
        upstream = cfg.get('Update', 'upstream')
        if not is_upstream_created(upstream):
            create_fork_upstream(upstream)
        print(f'{TERMINAL_YELLOW}git fetch {upstream}:{TERMINAL_DEFAULT}')
        process = subprocess.run(['git', 'fetch', upstream], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode == 0:
            print(process.stdout.decode())
            print(f'{TERMINAL_YELLOW}git checkout master:{TERMINAL_DEFAULT}')
            process = subprocess.run(['git', 'checkout', 'master'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode == 0:
                print(process.stdout.decode())
                print(f'{TERMINAL_YELLOW}git merge {upstream}/master:{TERMINAL_DEFAULT}')
                process = subprocess.run(['git', 'merge', f'{upstream}/master'],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if process.returncode == 0:
                    print(process.stdout.decode())
                    print(f'{TERMINAL_YELLOW}...    ...{TERMINAL_DEFAULT}')
                else:
                    print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
                    aborting_update()
                    sys.exit(1)
            else:
                print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
                aborting_update()
                sys.exit(0)
        else:
            print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
            aborting_update()
            sys.exit(0)

    else:
        print(f'{TERMINAL_YELLOW}Fork Auto-Update disabled in config file{TERMINAL_YELLOW}')
        aborting_update()
        sys.exit(0)


def get_git_current_tag(path_current_version):
    try:
        with open(path_current_version, 'r') as version_content:
            version = version_content.read()
    except FileNotFoundError:
        version = 'v5.0'  # TODO Replace with VERSION.json
        with open(path_current_version, 'w') as version_content:
            version_content.write(version)

    version = version.replace(" ", "").splitlines()[0]
    if version[0] != 'v':
        version = f'v{version}'
    return version

def _sort_version_tags(versions, current_version):
    tags = {}
    rcurrent_version = current_version.split('.')
    if len(rcurrent_version) == 2:
        curr_version, curr_subversion = rcurrent_version
        curr_sub_release = None
    else:  # len(rcurrent_version) == 3
        curr_version, curr_subversion, curr_sub_release = rcurrent_version
        curr_sub_release = int(curr_sub_release)
    curr_version = int(curr_version)
    curr_subversion = int(curr_subversion)

    for v in versions:
        ver = v.split('.')
        if len(ver) == 2:
            version, subversion = ver
            sub_release = None
        elif len(ver) == 3:
            version, subversion, sub_release = ver
            sub_release = int(sub_release)
        else:
            continue
        version = int(version[1:])
        subversion = int(subversion)
        if version not in tags:
            tags[version] = {}
        if subversion not in tags[version]:
            tags[version][subversion] = set()
        if sub_release is not None:
            tags[version][subversion].add(sub_release)

    sorted_versions = []
    for version in sorted(tags.keys()):
        if version < curr_version:
            continue
        for subversion in sorted(tags[version].keys()):
            if version == curr_version and subversion < curr_subversion:
                continue
            if tags[version][subversion]:
                r_tag = f'v{version}.{subversion}'
                if r_tag in versions:
                    if version != curr_version and subversion != curr_subversion:
                        sorted_versions.append(r_tag)
                for sub_release in sorted(tags[version][subversion]):
                    if curr_sub_release:
                        if version == curr_version and subversion == curr_subversion and sub_release < curr_sub_release:
                            continue
                    sorted_versions.append(f'v{version}.{subversion}.{sub_release}')
            else:
                if curr_version != version and subversion != curr_subversion:
                    sorted_versions.append(f'v{version}.{subversion}')
    if sorted_versions[0] == current_version:
        sorted_versions = sorted_versions[1:]
    return sorted_versions


def get_git_upper_tags_remote(current_tag, is_fork):
    if is_fork:
        process = subprocess.run(['git', 'tag'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode == 0:
            list_all_tags = process.stdout.decode().splitlines()

            list_upper_tags = _sort_version_tags(list_all_tags, current_tag)
            return list_upper_tags
        else:
            print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
            aborting_update()
            sys.exit(0)
    else:
        process = subprocess.run(['git', 'ls-remote', '--tags'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode == 0:
            list_all_tags = process.stdout.decode().splitlines()
            last_tag = list_all_tags[-1].split('\trefs/tags/')
            last_commit = last_tag[0]
            last_tag = last_tag[1].split('^{}')[0]
            list_upper_tags = []
            if last_tag[1:] == current_tag:
                return []
            else:
                dict_tags_commit = {}
                for mess_tag in list_all_tags:
                    commit, tag = mess_tag.split('\trefs/tags/')

                    tag = tag.replace('^{}', '')
                    # remove 'v' version
                    dict_tags_commit[tag] = commit

                sorted_tags = _sort_version_tags(dict_tags_commit.keys(), current_tag)
                list_upper_tags = [(key, dict_tags_commit[key]) for key in sorted_tags]
                return list_upper_tags
        else:
            print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
            aborting_update()
            sys.exit(0)

def update_ail(current_tag, list_upper_tags_remote, current_version_path, is_fork):
    print(f'{TERMINAL_YELLOW}git checkout master:{TERMINAL_DEFAULT}')
    process = subprocess.run(['git', 'checkout', 'master'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # process = subprocess.run(['ls'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        print(process.stdout.decode())
        print()

        temp_current_tag = current_tag.replace('v', '').split('.')[0]
        if float(temp_current_tag) < 5.0:
            roll_back_update('2c65194b94dab95df9b8da19c88d65239f398355')
            pulled = True
        else:
            print(f'{TERMINAL_YELLOW}git pull:{TERMINAL_DEFAULT}')
            process = subprocess.run(['git', 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode == 0:
                output = process.stdout.decode()
                print(output)
                pulled = True
            else:
                print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
                aborting_update()
                pulled = False
                sys.exit(1)

        if pulled:
            update_submodule()

            # CHECK IF UPDATER Update
            if float(os.stat(UPDATER_FILENAME).st_mtime) > UPDATER_LAST_MODIFICATION:
                # request updater relaunch
                print(f'{TERMINAL_RED}                  Relaunch Launcher                    {TERMINAL_DEFAULT}')
                sys.exit(3)

            # # EMERGENCY UPDATE between two tags
            # if len(list_upper_tags_remote) == 1:
            #     # additional update (between 2 commits on the same version)
            #     additional_update_path = os.path.join(os.environ['AIL_HOME'], 'update', current_tag, 'additional_update.sh')
            #     if os.path.isfile(additional_update_path):
            #         print()
            #         print(f'{TERMINAL_YELLOW}------------------------------------------------------------------')
            #         print('-                 Launching Additional Update:                   -')
            #         print(f'--  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --{TERMINAL_DEFAULT}')
            #         process = subprocess.run(['bash', additional_update_path],
            #                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #         if process.returncode == 0:
            #             output = process.stdout.decode()
            #             print(output)
            #         else:
            #             print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
            #             aborting_update()
            #             sys.exit(1)
            #
            #     print()
            #     print(f'{TERMINAL_YELLOW}****************  AIL Successfully Updated  *****************{TERMINAL_DEFAULT}')
            #     print()
            #     exit(0)

            if list_upper_tags_remote:
                for v_update in list_upper_tags_remote:
                    if is_fork:
                        version_tag = v_update
                    else:
                        version_tag = v_update[0]
                        previous_commit = v_update[1]
                    launch_update_version(version_tag, current_version_path, roll_back_commit=None, is_fork=is_fork)

                # Success
                print(f'{TERMINAL_YELLOW}****************  AIL Successfully Updated  *****************{TERMINAL_DEFAULT}')
                print()
                sys.exit(0)

    else:
        print(f'{TERMINAL_RED}{process.stderr.decode()}{TERMINAL_DEFAULT}')
        aborting_update()
        sys.exit(0)

def launch_update_version(version, current_version_path, roll_back_commit=None, is_fork=False):
    update_path = os.path.join(os.environ['AIL_HOME'], 'update', str(version), 'Update.sh')
    print()
    print(f'{TERMINAL_YELLOW}------------------------------------------------------------------')
    print(f'-                 Launching Update: {TERMINAL_BLUE}{version}{TERMINAL_YELLOW}                         -')
    print(f'--  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --{TERMINAL_DEFAULT}')
    if not os.path.isfile(update_path):
        update_path = os.path.join(os.environ['AIL_HOME'], 'update', 'default_update', 'Update.sh')
        process = subprocess.Popen(['bash', update_path, version], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(['bash', update_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    if process.returncode == 0:
        # output = process.stdout.decode()
        # print(output)

        with open(current_version_path, 'w') as version_content:
            version_content.write(version)

            print(f'{TERMINAL_YELLOW}--  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --')
            print(f'-               Successfully Updated: {TERMINAL_BLUE}{version}{TERMINAL_YELLOW}                        -')
            print(f'------------------------------------------------------------------{TERMINAL_DEFAULT}')
            print()
    else:
        # print(process.stdout.read().decode())
        print(f'{TERMINAL_RED}{process.stderr.read().decode()}{TERMINAL_DEFAULT}')
        print('------------------------------------------------------------------')
        print(f'                   {TERMINAL_RED}Update Error: {TERMINAL_BLUE}{version}{TERMINAL_DEFAULT}')
        print('------------------------------------------------------------------')
        if not is_fork and roll_back_commit:
            roll_back_update(roll_back_commit)
        else:
            aborting_update()
            sys.exit(1)

def roll_back_update(roll_back_commit):
    print(f'Rolling back to safe commit: {TERMINAL_BLUE}{roll_back_commit}{TERMINAL_DEFAULT}')
    process = subprocess.run(['git', 'checkout', roll_back_commit], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        output = process.stdout
        print(output)
        sys.exit(0)
    else:
        print(TERMINAL_RED+process.stderr.decode()+TERMINAL_DEFAULT)
        aborting_update()
        sys.exit(1)

def aborting_update():
    print()
    print(f'{TERMINAL_RED}Aborting ...{TERMINAL_DEFAULT}')
    print(f'{TERMINAL_RED}******************************************************************')
    print('*                    AIL Not Updated                             *')
    print(f'******************************************************************{TERMINAL_DEFAULT}')
    print()


if __name__ == "__main__":

    TERMINAL_RED = '\033[91m'
    TERMINAL_YELLOW = '\33[93m'
    TERMINAL_BLUE = '\33[94m'
    TERMINAL_BLINK = '\33[6m'
    TERMINAL_DEFAULT = '\033[0m'

    AIL_REPO = 'https://github.com/ail-project/ail-framework'
    AIL_REPO_NAME = 'ail-project/ail-framework.git'
    OLD_AIL_REPO = 'https://github.com/CIRCL/AIL-framework.git'

    configfile = os.path.join(os.environ['AIL_HOME'], 'configs/update.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    current_version_path = os.path.join(os.environ['AIL_HOME'], 'update/current_version')

    print(f'{TERMINAL_YELLOW}******************************************************************')
    print('*                        Updating AIL ...                        *')
    print(f'******************************************************************{TERMINAL_DEFAULT}')

    # manual updates
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", nargs='?', const=True, default=False)
    args = parser.parse_args()
    manual_update = args.manual

    if auto_update_enabled(cfg) or manual_update:
        update_submodule()
        if check_if_files_modified():
            is_fork = repo_is_fork()
            if is_fork:
                update_fork()

            current_tag = get_git_current_tag(current_version_path)
            print()
            print(f'Current Version: {TERMINAL_YELLOW}{current_tag}{TERMINAL_DEFAULT}')
            print()
            list_upper_tags_remote = get_git_upper_tags_remote(current_tag.replace('v', ''), is_fork)
            # new release
            if len(list_upper_tags_remote) > 0:
                print('New Releases:')
            if is_fork:
                for upper_tag in list_upper_tags_remote:
                    print(f'    {TERMINAL_BLUE}{upper_tag}{TERMINAL_DEFAULT}')
            else:
                for upper_tag in list_upper_tags_remote:
                    print(f'    {TERMINAL_BLUE}{upper_tag[0]}{TERMINAL_DEFAULT}: {upper_tag[1]}')
            update_ail(current_tag, list_upper_tags_remote, current_version_path, is_fork)

        else:
            print('Please, commit your changes or stash them before you can update AIL')
            aborting_update()
            sys.exit(0)
    else:
        print(f'               {TERMINAL_RED}AIL Auto update is disabled{TERMINAL_DEFAULT}')
        aborting_update()
        sys.exit(0)

    # r = get_git_upper_tags_remote('6.0', False)
    # print(r)

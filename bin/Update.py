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

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages')) # # TODO: move other functions
import git_status


UPDATER_FILENAME = os.path.join(os.environ['AIL_BIN'], 'Update.py')

UPDATER_LAST_MODIFICATION = float(os.stat(UPDATER_FILENAME).st_mtime)

def auto_update_enabled(cfg):
    auto_update = cfg.get('Update', 'auto_update')
    if auto_update == 'True' or auto_update == 'true':
        return True
    else:
        return False

# check if files are modify locally
def check_if_files_modified():
    process = subprocess.run(['git', 'ls-files' ,'-m'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
                    print('{}{}{}'.format(TERMINAL_BLUE, modified_file, TERMINAL_DEFAULT))
                print()
                return False
            else:
                return True
        else:
            return True
    else:
        print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        sys.exit(1)

def repo_is_fork():
    print('Check if this repository is a fork:')
    process = subprocess.run(['git', 'remote', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode == 0:
        res = process.stdout.decode()
        if 'origin	{}'.format(AIL_REPO) in res:
            print('    This repository is a {}clone of {}{}'.format(TERMINAL_BLUE, AIL_REPO, TERMINAL_DEFAULT))
            return False
        elif 'origin	{}'.format(OLD_AIL_REPO) in res:
            print('    old AIL repository, Updating remote origin...')
            res = git_status.set_default_remote(AIL_REPO, verbose=False)
            if res:
                return False
            else:
                return True
        else:
            print('    This repository is a {}fork{}'.format(TERMINAL_BLUE, TERMINAL_DEFAULT))
            print()
            return True
    else:
        print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
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
        print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        aborting_update()
        sys.exit(0)

def create_fork_upstream(upstream):
    print('{}... Creating upstream ...{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
    print('git remote add {} {}'.format(upstream, AIL_REPO))
    process = subprocess.run(['git', 'remote', 'add', upstream, AIL_REPO], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        print(process.stdout.decode())
        if is_upstream_created(upstream):
            print('Fork upstream created')
            print('{}...    ...{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
        else:
            print('Fork not created')
            aborting_update()
            sys.exit(0)
    else:
        print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        aborting_update()
        sys.exit(0)

def update_fork():
    print('{}... Updating fork ...{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
    if cfg.get('Update', 'update-fork') == 'True' or cfg.get('Update', 'update-fork') == 'true':
        upstream = cfg.get('Update', 'upstream')
        if not is_upstream_created(upstream):
            create_fork_upstream(upstream)
        print('{}git fetch {}:{}'.format(TERMINAL_YELLOW, upstream, TERMINAL_DEFAULT))
        process = subprocess.run(['git', 'fetch', upstream], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode == 0:
            print(process.stdout.decode())
            print('{}git checkout master:{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
            process = subprocess.run(['git', 'checkout', 'master'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode == 0:
                print(process.stdout.decode())
                print('{}git merge {}/master:{}'.format(TERMINAL_YELLOW, upstream, TERMINAL_DEFAULT))
                process = subprocess.run(['git', 'merge', '{}/master'.format(upstream)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if process.returncode == 0:
                    print(process.stdout.decode())
                    print('{}...    ...{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
                else:
                    print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
                    aborting_update()
                    sys.exit(1)
            else:
                print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
                aborting_update()
                sys.exit(0)
        else:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
            aborting_update()
            sys.exit(0)

    else:
        print('{}Fork Auto-Update disabled in config file{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
        aborting_update()
        sys.exit(0)


def get_git_current_tag(current_version_path):
    try:
        with open(current_version_path, 'r') as version_content:
            version = version_content.read()
    except FileNotFoundError:
        version = 'v1.4'
        with open(current_version_path, 'w') as version_content:
            version_content.write(version)

    version = version.replace(" ", "").splitlines()[0]
    if version[0] != 'v':
        version = 'v{}'.format(version)
    return version

def get_git_upper_tags_remote(current_tag, is_fork):
    # keep only first dot
    nb_dot = current_tag.count('.')
    if nb_dot > 0:
        nb_dot = nb_dot -1
    current_tag_val = current_tag.rsplit('.', nb_dot)
    current_tag_val = ''.join(current_tag_val)


    if is_fork:
        process = subprocess.run(['git', 'tag'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode == 0:
            list_all_tags = process.stdout.decode().splitlines()

            list_upper_tags = []
            if list_all_tags[-1][1:] == current_tag:
                list_upper_tags.append( (list_all_tags[-1], None) )
                # force update order
                list_upper_tags.sort()
                return list_upper_tags
            for tag in list_all_tags:
                if float(tag[1:]) >= float(current_tag_val):
                    list_upper_tags.append( (tag, None) )
            # force update order
            list_upper_tags.sort()
            return list_upper_tags
        else:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
            aborting_update()
            sys.exit(0)
    else:
        process = subprocess.run(['git', 'ls-remote' ,'--tags'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode == 0:
            list_all_tags = process.stdout.decode().splitlines()
            last_tag = list_all_tags[-1].split('\trefs/tags/')
            last_commit = last_tag[0]
            last_tag = last_tag[1].split('^{}')[0]
            list_upper_tags = []
            if last_tag[1:] == current_tag:
                list_upper_tags.append( (last_tag, last_commit) )
                # force update order
                list_upper_tags.sort()
                return list_upper_tags
            else:
                dict_tags_commit = {}
                for mess_tag in list_all_tags:
                    commit, tag = mess_tag.split('\trefs/tags/')

                    tag = tag.replace('^{}', '')
                    # remove 'v' version
                    tag = tag.replace('v', '')
                    # keep only first dot
                    nb_dot = tag.count('.')
                    if nb_dot > 0:
                        nb_dot = nb_dot -1
                    tag_val = tag.rsplit('.', nb_dot)
                    tag_val = ''.join(tag_val)

                    # check if tag is float
                    try:
                        tag_val = float(tag_val)
                    except ValueError:
                        continue

                    # add tag with last commit
                    if float(tag_val) >= float(current_tag_val):
                        dict_tags_commit[tag] = commit
                list_upper_tags = [('v{}'.format(key), dict_tags_commit[key]) for key in dict_tags_commit]
                # force update order
                list_upper_tags.sort()
                return list_upper_tags
        else:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
            aborting_update()
            sys.exit(0)

def update_submodules():
    print('{}git submodule update:{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
    process = subprocess.run(['git', 'submodule', 'update'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        print(process.stdout.decode())
        print()
    else:
        print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))

def update_ail(current_tag, list_upper_tags_remote, current_version_path, is_fork):
    print('{}git checkout master:{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
    process = subprocess.run(['git', 'checkout', 'master'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #process = subprocess.run(['ls'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        print(process.stdout.decode())
        print()

        update_submodules()

        print('{}git pull:{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
        process = subprocess.run(['git', 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode == 0:
            output = process.stdout.decode()
            print(output)

            # CHECK IF UPDATER Update
            if float(os.stat(UPDATER_FILENAME).st_mtime) > UPDATER_LAST_MODIFICATION:
                # request updater relauch
                print('{}{}{}'.format(TERMINAL_RED, '                  Relaunch Launcher                    ', TERMINAL_DEFAULT))
                sys.exit(3)

            if len(list_upper_tags_remote) == 1:
                # additional update (between 2 commits on the same version)
                additional_update_path = os.path.join(os.environ['AIL_HOME'], 'update', current_tag, 'additional_update.sh')
                if os.path.isfile(additional_update_path):
                    print()
                    print('{}------------------------------------------------------------------'.format(TERMINAL_YELLOW))
                    print('-                 Launching Additional Update:                   -')
                    print('--  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --{}'.format(TERMINAL_DEFAULT))
                    process = subprocess.run(['bash', additional_update_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if process.returncode == 0:
                        output = process.stdout.decode()
                        print(output)
                    else:
                        print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
                        aborting_update()
                        sys.exit(1)

                print()
                print('{}****************  AIL Sucessfully Updated  *****************{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
                print()
                exit(0)

            else:
                # map version with roll back commit
                list_update = []
                previous_commit = list_upper_tags_remote[0][1]
                for tuple in list_upper_tags_remote[1:]:
                    tag = tuple[0]
                    list_update.append( (tag, previous_commit) )
                    previous_commit = tuple[1]

                for update in list_update:
                    launch_update_version(update[0], update[1], current_version_path, is_fork)
                # Sucess
                print('{}****************  AIL Sucessfully Updated  *****************{}'.format(TERMINAL_YELLOW, TERMINAL_DEFAULT))
                print()
                sys.exit(0)
        else:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
            aborting_update()
            sys.exit(1)
    else:
        print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        aborting_update()
        sys.exit(0)

def launch_update_version(version, roll_back_commit, current_version_path, is_fork):
    update_path = os.path.join(os.environ['AIL_HOME'], 'update', str(version), 'Update.sh')
    print()
    print('{}------------------------------------------------------------------'.format(TERMINAL_YELLOW))
    print('-                 Launching Update: {}{}{}                         -'.format(TERMINAL_BLUE, version, TERMINAL_YELLOW))
    print('--  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --{}'.format(TERMINAL_DEFAULT))
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
        #output = process.stdout.decode()
        #print(output)

        with open(current_version_path, 'w') as version_content:
            version_content.write(version)

            print('{}--  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --'.format(TERMINAL_YELLOW))
            print('-               Sucessfully Updated: {}{}{}                        -'.format(TERMINAL_BLUE, version, TERMINAL_YELLOW))
            print('------------------------------------------------------------------{}'.format(TERMINAL_DEFAULT))
            print()
    else:
        #print(process.stdout.read().decode())
        print('{}{}{}'.format(TERMINAL_RED, process.stderr.read().decode(), TERMINAL_DEFAULT))
        print('------------------------------------------------------------------')
        print('                   {}Update Error: {}{}{}'.format(TERMINAL_RED, TERMINAL_BLUE, version, TERMINAL_DEFAULT))
        print('------------------------------------------------------------------')
        if not is_fork:
            roll_back_update(roll_back_commit)
        else:
            aborting_update()
            sys.exit(1)

def roll_back_update(roll_back_commit):
    print('Rolling back to safe commit: {}{}{}'.format(TERMINAL_BLUE ,roll_back_commit, TERMINAL_DEFAULT))
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
    print('{}Aborting ...{}'.format(TERMINAL_RED, TERMINAL_DEFAULT))
    print('{}******************************************************************'.format(TERMINAL_RED))
    print('*                    AIL Not Updated                             *')
    print('******************************************************************{}'.format(TERMINAL_DEFAULT))
    print()

if __name__ == "__main__":

    TERMINAL_RED = '\033[91m'
    TERMINAL_YELLOW = '\33[93m'
    TERMINAL_BLUE = '\33[94m'
    TERMINAL_BLINK = '\33[6m'
    TERMINAL_DEFAULT = '\033[0m'

    AIL_REPO = 'https://github.com/ail-project/ail-framework'
    OLD_AIL_REPO = 'https://github.com/CIRCL/AIL-framework.git'

    configfile = os.path.join(os.environ['AIL_HOME'], 'configs/update.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    current_version_path = os.path.join(os.environ['AIL_HOME'], 'update/current_version')

    print('{}******************************************************************'.format(TERMINAL_YELLOW))
    print('*                        Updating AIL ...                        *')
    print('******************************************************************{}'.format(TERMINAL_DEFAULT))

    # manual updates
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", nargs='?', const=True, default=False)
    args = parser.parse_args()
    manual_update = args.manual

    if auto_update_enabled(cfg) or manual_update:
        if check_if_files_modified():
            is_fork = repo_is_fork()
            if is_fork:
                update_fork()

            current_tag = get_git_current_tag(current_version_path)
            print()
            print('Current Version: {}{}{}'.format( TERMINAL_YELLOW, current_tag, TERMINAL_DEFAULT))
            print()
            list_upper_tags_remote = get_git_upper_tags_remote(current_tag.replace('v', ''), is_fork)
            # new realease
            if len(list_upper_tags_remote) > 1:
                print('New Releases:')
            if is_fork:
                for upper_tag in list_upper_tags_remote:
                    print('    {}{}{}'.format(TERMINAL_BLUE, upper_tag[0], TERMINAL_DEFAULT))
            else:
                for upper_tag in list_upper_tags_remote:
                    print('    {}{}{}: {}'.format(TERMINAL_BLUE, upper_tag[0], TERMINAL_DEFAULT, upper_tag[1]))
            print()
            update_ail(current_tag, list_upper_tags_remote, current_version_path, is_fork)

        else:
            print('Please, commit your changes or stash them before you can update AIL')
            aborting_update()
            sys.exit(0)
    else:
        print('               {}AIL Auto update is disabled{}'.format(TERMINAL_RED, TERMINAL_DEFAULT))
        aborting_update()
        sys.exit(0)

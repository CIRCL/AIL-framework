#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import configparser
import os
import sys

import subprocess

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
            return False
        else:
            return True
    else:
        print(TERMINAL_RED+process.stderr.decode()+TERMINAL_DEFAULT)
        return False

def repo_is_fork():
    process = subprocess.run(['git', 'ls-remote', '--tags'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode == 0:
        # remove url origin
        local_remote = process.stdout
        process = subprocess.run(['git', 'ls-remote' ,'--tags', AIL_REPO], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode == 0:
            ail_remote = process.stdout
            print(local_remote)
            print(ail_remote)
            if local_remote == ail_remote:
                return False
            else:
                return True
    else:
        print(TERMINAL_RED+process.stderr.decode()+TERMINAL_DEFAULT)
        return False

def is_upstream_created(upstream):
    process = subprocess.run(['git', 'remote', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        output = process.stdout.decode()
        if upstream in output:
            return True
        else:
            return False
    else:
        print(process.stderr.decode())
        return None

def create_fork_upstream(upstream):
    process = subprocess.run(['git', 'remote', 'add', upstream, AIL_REPO], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        print(process.stdout.decode())
        if is_upstream_created():
            print('fork created')
        else:
            print('error, fork not created')
    else:
        print(process.stderr.decode())
        return None

def update_fork():
    if cfg.get('Update', 'update-fork') == 'True' or cfg.get('Update', 'update-fork') == 'true':
        upstream = cfg.get('Update', 'upstream')
        if not is_upstream_created(upstream):
            create_fork_upstream(upstream)
        process = subprocess.run(['git', 'fetch', upstream], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode == 0:
            print(process.stdout.decode())
            process = subprocess.run(['git', 'checkout', 'master'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if process.returncode == 0:
                print(process.stdout.decode())
                process = subprocess.run(['git', 'merge', '{}/master'.format(upstream)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if process.returncode == 0:
                    print(process.stdout.decode())
                else:
                    print(process.stderr.decode())
                    return None
            else:
                print(process.stderr.decode())
                return None
        else:
            print(process.stderr.decode())
            return None

    else:
        print('auto update fork disabled, you can active it in ...')


def get_git_current_tag(current_version_path):
    with open(current_version_path, 'r') as version_content:
        version = version_content.read()
    version = version.replace(" ", "").splitlines()
    return version[0]

    '''
    process = subprocess.run(['git', 'describe' ,'--tags'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode == 0:
        current_tag = process.stdout
        current_tag = current_tag.split(b'-')[0]
        return current_tag.decode()
    else:
        print(process.stderr.decode())
        return None
    '''

def get_git_upper_tags_remote(current_tag):
    process = subprocess.run(['git', 'ls-remote' ,'--tags'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode == 0:
        list_all_tags = process.stdout.decode().splitlines()
        list_all_tags.append('aaaaaaaaaaaaaaaaaaaaaaaaaaaaa\trefs/tags/v1.5')
        list_all_tags.append('eeeeeeeeeeeeeeeeeeeeeeeeeeee\trefs/tags/v1.5^{}')
        list_all_tags.append('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\trefs/tags/v1.6')
        list_all_tags.append('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\trefs/tags/v1.6^{}')
        list_all_tags.append('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz\trefs/tags/v1.7')
        last_tag = list_all_tags[-1].split('\trefs/tags/')
        last_commit = last_tag[0]
        last_tag = last_tag[1].split('^{}')[0]
        list_upper_tags = []
        if last_tag[1:] == current_tag:
            list_upper_tags.append( (last_tag, last_commit) )
            return list_upper_tags
        else:
            for mess_tag in list_all_tags:
                commit, tag = mess_tag.split('\trefs/tags/')

                # add tag with last commit
                if float(tag.split('^{}')[0][1:]) >= float(current_tag):
                    if '^{}' in tag:
                        list_upper_tags.append( (tag.split('^{}')[0], commit) )
            # add last commit
            if last_tag not in list_upper_tags[-1][0]:
                list_upper_tags.append( (last_tag, last_commit) )
            return list_upper_tags

    else:
        print(TERMINAL_RED+process.stderr.decode()+TERMINAL_DEFAULT)
        return None

def update_ail(current_tag, list_upper_tags_remote, current_version_path):
    print('git checkout master:')
    process = subprocess.run(['git', 'checkout', 'master'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if process.returncode == 0:
        print('git pull:')
        process = subprocess.run(['git', 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if process.returncode == 0:
            output = process.stdout.decode()
            print(output)

            if len(list_upper_tags_remote) == 1:
                print('AIL Updated')
                # # FIXME: # TODO: exit sucess

            else:
                # map version with roll back commit
                list_update = []
                previous_commit = list_upper_tags_remote[0][1]
                for tuple in list_upper_tags_remote[1:]:
                    tag = tuple[0]
                    list_update.append( (tag, previous_commit) )
                    previous_commit = tuple[1]
                print(list_update)

                for update in list_update:
                    launch_update_version(update[0], update[1], current_version_path, is_fork)
        else:
            print(TERMINAL_RED+process.stderr.decode()+TERMINAL_DEFAULT)
            return None
    else:
        print(TERMINAL_RED+process.stderr.decode()+TERMINAL_DEFAULT)
        return None

def launch_update_version(version, roll_back_commit, current_version_path, is_fork):
    update_path = os.path.join(os.environ['AIL_HOME'], 'update', version, 'Update.sh')
    print('------------------------------------------------------------------')
    print('-                 Launching Update: {}                           -'.format(version))
    print('------------------------------------------------------------------')
    process = subprocess.run(['bash', update_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        output = process.stdout
        print(output)

        with open(current_version_path, 'w') as version_content:
            version_content.write(version)

    else:
        print(TERMINAL_RED+process.stderr.decode()+TERMINAL_DEFAULT)
        if not is_fork:
            roll_back_update(roll_back_commit)

def roll_back_update(roll_back_commit):
    process = subprocess.run(['git', 'checkout', roll_back_commit], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        output = process.stdout
        print(output)
        sys.exit()
    else:
        print(TERMINAL_RED+process.stderr.decode()+TERMINAL_DEFAULT)
        sys.exit(1)

'''

    if len(sys.argv) != 2:
        print('usage:', 'Update-conf.py', 'Automatic (boolean)')
        exit(1)
    else:
        automatic = sys.argv[1]
        if automatic == 'True':
            automatic = True
        else:
            automatic = False


    if automatic:
        resp = 'y'
    else:
        resp = input("Do you want to auto fix it? [y/n] ")

    if resp != 'y':
        return False
    else:
        if automatic:
            resp2 = 'y'
        else:
            resp2 = input("Do you want to keep a backup of the old configuration file? [y/n] ")
'''

if __name__ == "__main__":

    TERMINAL_RED = '\033[91m'
    TERMINAL_YELLOW = '\33[93m'
    TERMINAL_DEFAULT = '\033[0m'

    AIL_REPO = 'https://github.com/CIRCL/AIL-framework.git'

    configfile = os.path.join(os.environ['AIL_HOME'], 'configs/update.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    current_version_path = os.path.join(os.environ['AIL_HOME'], 'update/current_version')

    print('******************************************************************')
    print('*                        Updating AIL ...                        *')
    print('******************************************************************')

    if auto_update_enabled(cfg):
        if check_if_files_modified():
            is_fork = repo_is_fork()
            if is_fork:
                update_fork()

            current_tag = get_git_current_tag(current_version_path)
            print('Current Version: {}'.format(current_tag))
            print()
            list_upper_tags_remote = get_git_upper_tags_remote(current_tag[1:])
            # new realease
            if len(list_upper_tags_remote) > 1:
                print('New Releases:')
            for upper_tag in list_upper_tags_remote:
                print('    {}{}{}: {}'.format(TERMINAL_YELLOW, upper_tag[0], TERMINAL_DEFAULT, upper_tag[1]))
            print()
            update_ail(current_tag, list_upper_tags_remote, current_version_path, is_fork)
            #else:
            #    print('your fork is outdated')
        else:
            print('please commit your change')
    else:
        print('               AIL Auto update is disabled')
        print('                     AIL not Updated')
        print('******************************************************************')
    '''
    if main():
        sys.exit()
    else:
        sys.exit(1)
    '''

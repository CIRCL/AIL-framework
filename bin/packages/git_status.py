#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import subprocess

TERMINAL_RED = '\033[91m'
TERMINAL_YELLOW = '\33[93m'
TERMINAL_BLUE = '\33[94m'
TERMINAL_BLINK = '\33[6m'
TERMINAL_DEFAULT = '\033[0m'

REPO_ORIGIN = 'https://github.com/ail-project/ail-framework.git'

# set defaut_remote
def set_default_remote(new_origin_url, verbose=False):
    process = subprocess.run(['git', 'remote', 'set-url', 'origin', new_origin_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        res = process.stdout
        if res == b'':
            return True
        else:
            return False
    else:
        if verbose:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        return False

# Check if working directory is clean
def is_working_directory_clean(verbose=False):
    if verbose:
        print('check if this git directory is clean ...')
        #print('git ls-files -m')
    process = subprocess.run(['git', 'ls-files', '-m'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        res = process.stdout
        if res == b'':
            return True
        else:
            return False
    else:
        if verbose:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        return False

# Check if this git is a fork
def is_not_fork(origin_repo, verbose=False):
    if verbose:
        print('check if this git is a fork ...')
        #print('git remote -v')
    process = subprocess.run(['git', 'remote', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        res = process.stdout.decode()
        if verbose:
            print(res)
        if 'origin	{}'.format(origin_repo) in res:
            return True
        else:
            return False
    else:
        if verbose:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        return False

# Get current branch
def get_current_branch(verbose=False):
    if verbose:
        print('retrieving current branch ...')
        #print('git rev-parse --abbrev-ref HEAD')
    process = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        current_branch = process.stdout.replace(b'\n', b'').decode()
        if verbose:
            print(current_branch)
        return current_branch

    else:
        if verbose:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        return ''

# Get last commit id on master branch from remote
def get_last_commit_id_from_remote(branch='master', verbose=False):
    if verbose:
        print('retrieving last remote commit id ...')
        #print('git ls-remote origin master')
    process = subprocess.run(['git', 'ls-remote', 'origin', branch], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        last_commit_id = process.stdout.split(b'\t')[0].replace(b'\n', b'').decode()
        if verbose:
            print(last_commit_id)
        return last_commit_id

    else:
        if verbose:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        return ''

# Get last commit id on master branch from local
def get_last_commit_id_from_local(branch='master', verbose=False):
    if verbose:
        print('retrieving last local commit id ...')
        #print('git rev-parse master')
    process = subprocess.run(['git', 'rev-parse', branch], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        last_commit_id = process.stdout.replace(b'\n', b'').decode()
        if verbose:
            print(last_commit_id)
        return last_commit_id

    else:
        if verbose:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        return ''

# Get last local tag
def get_last_tag_from_local(verbose=False):
    if verbose:
        print('retrieving last local tag ...')
        #print('git describe --abbrev=0 --tags')
    process = subprocess.run(['git', 'describe', '--abbrev=0', '--tags'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        last_local_tag = process.stdout.replace(b'\n', b'').decode()
        if verbose:
            print(last_local_tag)
        return last_local_tag

    else:
        if verbose:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        return ''

# Get last remote tag
def get_last_tag_from_remote(verbose=False):
    if verbose:
        print('retrieving last remote tag ...')
        #print('git ls-remote --tags')

    process = subprocess.run(['git', 'ls-remote', '--tags'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        output_lines = process.stdout.split(b'\n')
        if len(output_lines) > 1:
            # Assuming we want the second-to-last line as before
            res = output_lines[-2].split(b'/')[-1].replace(b'^{}', b'').decode()
            if verbose:
                print(res)
            return res
        else:
            if verbose:
                print("No tags found or insufficient output from git command.")
            return ''

    else:
        if verbose:
            print('{}{}{}'.format(TERMINAL_RED, process.stderr.decode(), TERMINAL_DEFAULT))
        return ''

def get_git_metadata():
    dict_git = {}
    dict_git['current_branch'] = get_current_branch()
    dict_git['is_clone'] = is_not_fork(REPO_ORIGIN)
    dict_git['is_working_directory_clean'] = is_working_directory_clean()
    dict_git['current_commit'] = get_last_commit_id_from_local()
    dict_git['last_remote_commit'] = get_last_commit_id_from_remote()
    dict_git['last_local_tag'] = get_last_tag_from_local()
    dict_git['last_remote_tag'] = get_last_tag_from_remote()

    if dict_git['current_commit'] != dict_git['last_remote_commit']:
        dict_git['new_git_update_available'] = True
    else:
        dict_git['new_git_update_available'] = False

    if dict_git['last_local_tag'] != dict_git['last_remote_tag']:
        dict_git['new_git_version_available'] = True
    else:
        dict_git['new_git_version_available'] = False

    return dict_git

if __name__ == "__main__":
    get_last_commit_id_from_remote(verbose=True)
    get_last_commit_id_from_local(verbose=True)
    get_last_tag_from_local(verbose=True)
    get_current_branch(verbose=True)
    print(is_fork('https://github.com/ail-project/ail-framework.git'))
    print(is_working_directory_clean())
    get_last_tag_from_remote(verbose=True)

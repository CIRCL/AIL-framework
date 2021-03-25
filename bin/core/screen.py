#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import subprocess
import sys
import re

all_screen_name = set()

def is_screen_install():
    cmd = ['screen', '-v']
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stdout:
        if p.stdout[:14] == b'Screen version':
            return True
    print(p.stderr)
    return False

def exist_screen(screen_name, with_sudoer=False):
    if with_sudoer:
        cmd_1 = ['sudo', 'screen', '-ls']
    else:
        cmd_1 = ['screen', '-ls']
    cmd_2 = ['egrep', '[0-9]+.{}'.format(screen_name)]
    p1 = subprocess.Popen(cmd_1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd_2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    output = p2.communicate()[0]
    if output:
        return True
    return False

def get_screen_pid(screen_name,  with_sudoer=False):
    if with_sudoer:
        cmd_1 = ['sudo', 'screen', '-ls']
    else:
        cmd_1 = ['screen', '-ls']
    cmd_2 = ['egrep', '[0-9]+.{}'.format(screen_name)]
    p1 = subprocess.Popen(cmd_1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd_2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    output = p2.communicate()[0]
    if output:
        # extract pids with screen name
        regex_pid_screen_name = b'[0-9]+.' + screen_name.encode()
        pids = re.findall(regex_pid_screen_name, output)
        # extract pids
        all_pids = []
        for pid_name in pids:
            pid = pid_name.split(b'.')[0].decode()
            all_pids.append(pid)
        return all_pids
    return []

def detach_screen(screen_name):
    cmd = ['screen', '-d', screen_name]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #if p.stdout:
    #    print(p.stdout)
    if p.stderr:
        print(p.stderr)

def create_screen(screen_name):
    if not exist_screen(screen_name):
        cmd = ['screen', '-dmS', screen_name]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not p.stderr:
            all_screen_name.add(screen_name)
            return True
        else:
            print(p.stderr)
    return False

def kill_screen(screen_name, with_sudoer=False):
    if get_screen_pid(screen_name, with_sudoer=with_sudoer):
        for pid in get_screen_pid(screen_name,  with_sudoer=with_sudoer):
            cmd = ['kill', pid]
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if p.stderr:
                print(p.stderr)
            else:
                print('{} killed'.format(pid))
        return True
    return False

# # TODO: add check if len(window_name) == 20
# use: screen -S 'pid.screen_name' -p %window_id% -Q title
# if len(windows_name) > 20 (truncated by default)
def get_screen_windows_list(screen_name, r_set=True):
    # detach screen to avoid incomplete result
    detach_screen(screen_name)
    if r_set:
        all_windows_name = set()
    else:
        all_windows_name = []
    cmd = ['screen', '-S', screen_name, '-Q', 'windows']
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stdout:
        for window_row in p.stdout.split(b'  '):
            window_id, window_name = window_row.decode().split()
            #print(window_id)
            #print(window_name)
            #print('---')
            if r_set:
                all_windows_name.add(window_name)
            else:
                all_windows_name.append(window_name)
    if p.stderr:
        print(p.stderr)
    return all_windows_name

def get_screen_windows_id(screen_name):
    # detach screen to avoid incomplete result
    detach_screen(screen_name)
    all_windows_id = {}
    cmd = ['screen', '-S', screen_name, '-Q', 'windows']
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stdout:
        for window_row in p.stdout.split(b'  '):
            window_id, window_name = window_row.decode().split()
            if window_name not in all_windows_id:
                all_windows_id[window_name] = []
            all_windows_id[window_name].append(window_id)
    if p.stderr:
        print(p.stderr)
    return all_windows_id

# script_location ${AIL_BIN}
def launch_windows_script(screen_name, window_name, dir_project, script_location, script_name, script_options=''):
    venv = os.path.join(dir_project, 'AILENV/bin/python')
    cmd = ['screen', '-S', screen_name, '-X', 'screen', '-t', window_name, 'bash', '-c', 'cd {}; ./{} {}; read x'.format(script_location,  script_name, script_options)]
    print(cmd)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(p.stdout)
    print(p.stderr)

def launch_uniq_windows_script(screen_name, window_name, dir_project, script_location, script_name, script_options='', kill_previous_windows=False):
    all_screen_name = get_screen_windows_id(screen_name)
    if window_name in all_screen_name:
        if kill_previous_windows:
            kill_screen_window(screen_name, all_screen_name[window_name][0], force=True)
        else:
            print('Error: screen {} already contain a windows with this name {}'.format(screen_name, window_name))
            return None
    launch_windows_script(screen_name, window_name, dir_project, script_location, script_name, script_options=script_options)

def kill_screen_window(screen_name, window_id, force=False):
    if force:# kill
        cmd = ['screen', '-S', screen_name, '-p', window_id, '-X', 'kill']
    else:# send ctr-C
        cmd = ['screen', '-S', screen_name, '-p', window_id, '-X', 'stuff', "$'\003'"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(p.stdout)
    print(p.stderr)

if __name__ == '__main__':
    res = get_screen_windows_list('Script_AIL')
    print(res)

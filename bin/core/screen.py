#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import subprocess
import sys

all_screen_name = set()

def is_screen_install():
    cmd = ['screen', '-v']
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stdout:
        if p.stdout[:14] == b'Screen version':
            return True
    print(p.stderr)
    return False

def exist_screen(screen_name):
    cmd_1 = ['screen', '-ls']
    cmd_2 = ['egrep', '[0-9]+.{}'.format(screen_name)]
    p1 = subprocess.Popen(cmd_1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd_2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    output = p2.communicate()[0]
    if output:
        return True
    return False

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

# # TODO: add check if len(window_name) == 20
# use: screen -S 'pid.screen_name' -p %window_id% -Q title
# if len(windows_name) > 20 (truncated by default)
def get_screen_windows_list(screen_name):
    cmd = ['screen', '-S', screen_name, '-Q', 'windows']
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stdout:
        for window_row in p.stdout.split(b'  '):
            window_id, window_name = window_row.decode().split()
            print(window_id)
            print(window_name)
            print('---')

# script_location ${AIL_BIN}
def launch_windows_script(screen_name, window_name, dir_project, script_location, script_name, script_options=''):
    venv = os.path.join(dir_project, 'AILENV/bin/python')
    cmd = ['screen', '-S', screen_name, '-X', 'screen', '-t', window_name, 'bash', '-c', 'cd {}; ./{} {}; read x'.format(script_location,  script_name, script_options)]
    print(cmd)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(p.stdout)
    print(p.stderr)

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

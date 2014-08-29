#!/usr/bin/env python2
# -*-coding:UTF-8 -*


import ConfigParser
import os
import subprocess

if __name__ == '__main__':
    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/modules.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    config = ConfigParser.ConfigParser()
    config.read(configfile)

    modules = config.sections()
    for module in modules:
        subprocess.Popen(["python", './QueueIn.py', '-c', module])
        subprocess.Popen(["python", './QueueOut.py', '-c', module])
        #subprocess.Popen(["python", './{}.py'.format(module)])

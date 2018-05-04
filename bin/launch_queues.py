#!/usr/bin/env python3
# -*-coding:UTF-8 -*


import configparser
import os
import subprocess
import time


def check_pid(pid):
    if pid is None:
        # Already seen as finished.
        return None
    else:
        if pid.poll() is not None:
            return False
    return True

if __name__ == '__main__':
    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/modules.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    config = configparser.ConfigParser()
    config.read(configfile)

    modules = config.sections()
    pids = {}
    for module in modules:
        pin = subprocess.Popen(["python3", './QueueIn.py', '-c', module])
        pout = subprocess.Popen(["python3", './QueueOut.py', '-c', module])
        pids[module] = (pin, pout)
    is_running = True
    try:
        while is_running:
            time.sleep(5)
            is_running = False
            for module, p in pids.items():
                pin, pout = p
                if pin is None:
                    # already dead
                    pass
                elif not check_pid(pin):
                    print(module, 'input queue finished.')
                    pin = None
                else:
                    is_running = True
                if pout is None:
                    # already dead
                    pass
                elif not check_pid(pout):
                    print(module, 'output queue finished.')
                    pout = None
                else:
                    is_running = True
                pids[module] = (pin, pout)
    except KeyboardInterrupt:
        for module, p in pids.items():
            pin, pout = p
            if pin is not None:
                pin.kill()
            if pout is not None:
                pout.kill()

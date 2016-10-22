#!/usr/bin/env python2
# -*-coding:UTF-8 -*

'''

This module can be use to see information of running modules.
These information are logged in "logs/moduleInfo.log"

It can also try to manage them by killing inactive one.
However, it does not support mutliple occurence of the same module
(It will kill the first one obtained by get)


'''

import time
import datetime
import redis
import os
import signal
import argparse
from subprocess import PIPE, Popen
import ConfigParser
import json
from terminaltables import AsciiTable
import textwrap

# CONFIG VARIABLES
threshold_stucked_module = 60*60*1 #1 hour
log_filename = "../logs/moduleInfo.log"
command_search_pid = "ps a -o pid,cmd | grep {}"
command_search_name = "ps a -o pid,cmd | grep {}"
command_restart_module = "screen -S \"Script\" -X screen -t \"{}\" bash -c \"./{}.py; read x\""


def getPid(module):
    p = Popen([command_search_pid.format(module+".py")], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
    for line in p.stdout:
        splittedLine = line.split()
        if 'python2' in splittedLine:
            return int(splittedLine[0])
        else:
            return None

def clearRedisModuleInfo():
    for k in server.keys("MODULE_*"):
        server.delete(k)

def cleanRedis():
    for k in server.keys("MODULE_TYPE_*"):
        moduleName = k[12:].split('_')[0]
        for pid in server.smembers(k):
            flag_pid_valid = False
            proc = Popen([command_search_name.format(pid)], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
            for line in proc.stdout:
                splittedLine = line.split()
                if ('python2' in splittedLine or 'python' in splittedLine) and "./"+moduleName+".py" in splittedLine:
                    flag_pid_valid = True

            if not flag_pid_valid:
                print flag_pid_valid, 'cleaning', pid, 'in', k
                server.srem(k, pid)
                time.sleep(5)


def kill_module(module):
    print ''
    print '-> trying to kill module:', module

    pid = getPid(module)
    if pid is not None:
        os.kill(pid, signal.SIGUSR1)
        time.sleep(1)
        if getPid(module) is None:
            print module, 'has been killed'
            print 'restarting', module, '...'
            p2 = Popen([command_restart_module.format(module, module)], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)

        else:
            print 'killing failed, retrying...'
            time.sleep(3)
            os.kill(pid, signal.SIGUSR1)
            time.sleep(1)
            if getPid(module) is None:
                print module, 'has been killed'
                print 'restarting', module, '...'
                p2 = Popen([command_restart_module.format(module, module)], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
            else:
                print 'killing failed!'
    time.sleep(7)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Show info concerning running modules and log suspected stucked modules. May be use to automatically kill and restart stucked one.')
    parser.add_argument('-r', '--refresh', type=int, required=False, default=1, help='Refresh rate')
    parser.add_argument('-k', '--autokill', type=int, required=False, default=0, help='Enable auto kill option (1 for TRUE, anything else for FALSE)')
    parser.add_argument('-c', '--clear', type=int, required=False, default=0, help='Clear the current module information (Used to clear data from old launched modules)')

    args = parser.parse_args()

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)

    # REDIS #
    server = redis.StrictRedis(
        host=cfg.get("Redis_Queues", "host"),
        port=cfg.getint("Redis_Queues", "port"),
        db=cfg.getint("Redis_Queues", "db"))

    if args.clear == 1:
        clearRedisModuleInfo()

    lastTime = datetime.datetime.now()

    module_file_array = set()
    path_allmod = os.path.join(os.environ['AIL_HOME'], 'doc/all_modules.txt')
    with open(path_allmod, 'r') as module_file:
        for line in module_file:
            module_file_array.add(line[:-1])

        while True:

            all_queue = set()
            printarray1 = []
            printarray2 = []
            printarray3 = []
            for queue, card in server.hgetall("queues").iteritems():
                all_queue.add(queue)
                key = "MODULE_" + queue + "_"
                keySet = "MODULE_TYPE_" + queue

                for moduleNum in server.smembers(keySet):
                    value = server.get(key + str(moduleNum))
                    if value is not None:
                        timestamp, path = value.split(", ")
                        if timestamp is not None and path is not None:
                            startTime_readable = datetime.datetime.fromtimestamp(int(timestamp))
                            processed_time_readable = str((datetime.datetime.now() - startTime_readable)).split('.')[0]

                            if int(card) > 0:
                                if int((datetime.datetime.now() - startTime_readable).total_seconds()) > threshold_stucked_module:
                                    log = open(log_filename, 'a')
                                    log.write(json.dumps([queue, card, str(startTime_readable), str(processed_time_readable), path]) + "\n")
                                    if args.autokill == 1:
                                        kill_module(queue)

                                printarray1.append([str(queue), str(moduleNum), str(card), str(startTime_readable), str(processed_time_readable), str(path)])

                            else:
                                printarray2.append([str(queue), str(moduleNum), str(card), str(startTime_readable), str(processed_time_readable), str(path)])

            for curr_queue in module_file_array:
                if curr_queue not in all_queue:
                    printarray3.append([curr_queue, "Not running"])

            printarray1.sort(lambda x,y: cmp(x[4], y[4]), reverse=True)
            printarray2.sort(lambda x,y: cmp(x[4], y[4]), reverse=True)
            printarray1.insert(0,["Queue", "PID", "Amount", "Paste start time", "Processing time for current paste (H:M:S)", "Paste hash"])
            printarray2.insert(0,["Queue", "PID","Amount", "Paste start time", "Time since idle (H:M:S)", "Last paste hash"])
            printarray3.insert(0,["Queue", "State"])

            os.system('clear')
            t1 = AsciiTable(printarray1, title="Working queues")
            t1.column_max_width(1)
            if not t1.ok:
                    longest_col = t1.column_widths.index(max(t1.column_widths))
                    max_length_col = t1.column_max_width(longest_col)
                    if max_length_col > 0:
                        for i, content in enumerate(t1.table_data):
                            if len(content[longest_col]) > max_length_col:
                                temp = ''
                                for l in content[longest_col].splitlines():
                                    if len(l) > max_length_col:
                                        temp += '\n'.join(textwrap.wrap(l, max_length_col)) + '\n'
                                    else:
                                        temp += l + '\n'
                                    content[longest_col] = temp.strip()
                            t1.table_data[i] = content

            t2 = AsciiTable(printarray2, title="Idling queues")
            t2.column_max_width(1)
            if not t2.ok:
                    longest_col = t2.column_widths.index(max(t2.column_widths))
                    max_length_col = t2.column_max_width(longest_col)
                    if max_length_col > 0:
                        for i, content in enumerate(t2.table_data):
                            if len(content[longest_col]) > max_length_col:
                                temp = ''
                                for l in content[longest_col].splitlines():
                                    if len(l) > max_length_col:
                                        temp += '\n'.join(textwrap.wrap(l, max_length_col)) + '\n'
                                    else:
                                        temp += l + '\n'
                                    content[longest_col] = temp.strip()
                            t2.table_data[i] = content

            t3 = AsciiTable(printarray3, title="Not running queues")
            t3.column_max_width(1)

            print t1.table
            print '\n'
            print t2.table
            print '\n'
            print t3.table

            if (datetime.datetime.now() - lastTime).total_seconds() > args.refresh*5: 
                lastTime = datetime.datetime.now()
                cleanRedis()
            time.sleep(args.refresh)

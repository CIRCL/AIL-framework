#!/usr/bin/env python3
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
import configparser
import json
from terminaltables import AsciiTable
import textwrap
from colorama import Fore, Back, Style, init
import curses

# CONFIG VARIABLES
kill_retry_threshold = 60 #1m
log_filename = "../logs/moduleInfo.log"
command_search_pid = "ps a -o pid,cmd | grep {}"
command_search_name = "ps a -o pid,cmd | grep {}"
command_restart_module = "screen -S \"Script\" -X screen -t \"{}\" bash -c \"./{}.py; read x\""

init() #Necesary for colorama
printarrayGlob = [None]*14
printarrayGlob.insert(0, ["Time", "Module", "PID", "Action"])
lastTimeKillCommand = {}

#Curses init
#stdscr = curses.initscr()
#curses.cbreak()
#stdscr.keypad(1)

# GLOBAL
last_refresh = 0


def getPid(module):
    p = Popen([command_search_pid.format(module+".py")], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
    for line in p.stdout:
        print(line)
        splittedLine = line.split()
        if 'python2' in splittedLine:
            return int(splittedLine[0])
    return None

def clearRedisModuleInfo():
    for k in server.keys("MODULE_*"):
        server.delete(k)
    inst_time = datetime.datetime.fromtimestamp(int(time.time()))
    printarrayGlob.insert(1, [inst_time, "*", "-", "Cleared redis module info"])
    printarrayGlob.pop()

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
                print(flag_pid_valid, 'cleaning', pid, 'in', k)
                server.srem(k, pid)
                inst_time = datetime.datetime.fromtimestamp(int(time.time()))
                printarrayGlob.insert(1, [inst_time, moduleName, pid, "Cleared invalid pid in " + k])
                printarrayGlob.pop()
                #time.sleep(5)


def kill_module(module, pid):
    print('')
    print('-> trying to kill module:', module)

    if pid is None:
        print('pid was None')
        printarrayGlob.insert(1, [0, module, pid, "PID was None"])
        printarrayGlob.pop()
        pid = getPid(module)
    else: #Verify that the pid is at least in redis
        if server.exists("MODULE_"+module+"_"+str(pid)) == 0:
            return

    lastTimeKillCommand[pid] = int(time.time())
    if pid is not None:
        try:
            os.kill(pid, signal.SIGUSR1)
        except OSError:
            print(pid, 'already killed')
            inst_time = datetime.datetime.fromtimestamp(int(time.time()))
            printarrayGlob.insert(1, [inst_time, module, pid, "Already killed"])
            printarrayGlob.pop()
            return
        time.sleep(1)
        if getPid(module) is None:
            print(module, 'has been killed')
            print('restarting', module, '...')
            p2 = Popen([command_restart_module.format(module, module)], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
            inst_time = datetime.datetime.fromtimestamp(int(time.time()))
            printarrayGlob.insert(1, [inst_time, module, pid, "Killed"])
            printarrayGlob.insert(1, [inst_time, module, "?", "Restarted"])
            printarrayGlob.pop()
            printarrayGlob.pop()

        else:
            print('killing failed, retrying...')
            inst_time = datetime.datetime.fromtimestamp(int(time.time()))
            printarrayGlob.insert(1, [inst_time, module, pid, "Killing #1 failed."])
            printarrayGlob.pop()

            time.sleep(1)
            os.kill(pid, signal.SIGUSR1)
            time.sleep(1)
            if getPid(module) is None:
                print(module, 'has been killed')
                print('restarting', module, '...')
                p2 = Popen([command_restart_module.format(module, module)], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
                inst_time = datetime.datetime.fromtimestamp(int(time.time()))
                printarrayGlob.insert(1, [inst_time, module, pid, "Killed"])
                printarrayGlob.insert(1, [inst_time, module, "?", "Restarted"])
                printarrayGlob.pop()
                printarrayGlob.pop()
            else:
                print('killing failed!')
                inst_time = datetime.datetime.fromtimestamp(int(time.time()))
                printarrayGlob.insert(1, [inst_time, module, pid, "Killing failed!"])
                printarrayGlob.pop()
    else:
        print('Module does not exist')
        inst_time = datetime.datetime.fromtimestamp(int(time.time()))
        printarrayGlob.insert(1, [inst_time, module, pid, "Killing failed, module not found"])
        printarrayGlob.pop()
    #time.sleep(5)
    cleanRedis()

def get_color(time, idle):
    if time is not None:
        temp = time.split(':')
        time = int(temp[0])*3600 + int(temp[1])*60 + int(temp[2])

        if time >= args.treshold:
            if not idle:
                return Back.RED + Style.BRIGHT
            else:
                return Back.MAGENTA + Style.BRIGHT
        elif time > args.treshold/2:
            return Back.YELLOW + Style.BRIGHT
        else:
            return Back.GREEN + Style.BRIGHT
    else:
        return Style.RESET_ALL

def waiting_refresh():
    global last_refresh
    if time.time() - last_refresh < args.refresh:
        return False
    else:
        last_refresh = time.time()
        return True



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Show info concerning running modules and log suspected stucked modules. May be use to automatically kill and restart stucked one.')
    parser.add_argument('-r', '--refresh', type=int, required=False, default=1, help='Refresh rate')
    parser.add_argument('-t', '--treshold', type=int, required=False, default=60*10*1, help='Refresh rate')
    parser.add_argument('-k', '--autokill', type=int, required=False, default=0, help='Enable auto kill option (1 for TRUE, anything else for FALSE)')
    parser.add_argument('-c', '--clear', type=int, required=False, default=0, help='Clear the current module information (Used to clear data from old launched modules)')

    args = parser.parse_args()

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    cfg = configparser.ConfigParser()
    cfg.read(configfile)

    # REDIS #
    server = redis.StrictRedis(
        host=cfg.get("Redis_Queues", "host"),
        port=cfg.getint("Redis_Queues", "port"),
        db=cfg.getint("Redis_Queues", "db"),
        decode_responses=True)

    if args.clear == 1:
        clearRedisModuleInfo()

    lastTime = datetime.datetime.now()

    module_file_array = set()
    no_info_modules = {}
    path_allmod = os.path.join(os.environ['AIL_HOME'], 'doc/all_modules.txt')
    with open(path_allmod, 'r') as module_file:
        for line in module_file:
            module_file_array.add(line[:-1])

        cleanRedis()

        while True:
            if waiting_refresh():

                #key = ''
                #while key != 'q':
                #    key = stdsrc.getch()
                #    stdscr.refresh()

                all_queue = set()
                printarray1 = []
                printarray2 = []
                printarray3 = []
                for queue, card in server.hgetall("queues").items():
                    all_queue.add(queue)
                    key = "MODULE_" + queue + "_"
                    keySet = "MODULE_TYPE_" + queue
                    array_module_type = []

                    for moduleNum in server.smembers(keySet):
                        value = server.get(key + str(moduleNum))
                        if value is not None:
                            timestamp, path = value.split(", ")
                            if timestamp is not None and path is not None:
                                startTime_readable = datetime.datetime.fromtimestamp(int(timestamp))
                                processed_time_readable = str((datetime.datetime.now() - startTime_readable)).split('.')[0]

                                if int(card) > 0:
                                    if int((datetime.datetime.now() - startTime_readable).total_seconds()) > args.treshold:
                                        log = open(log_filename, 'a')
                                        log.write(json.dumps([queue, card, str(startTime_readable), str(processed_time_readable), path]) + "\n")
                                        try:
                                            last_kill_try = time.time() - lastTimeKillCommand[moduleNum]
                                        except KeyError:
                                            last_kill_try = kill_retry_threshold+1
                                        if args.autokill == 1 and last_kill_try > kill_retry_threshold :
                                            kill_module(queue, int(moduleNum))

                                    array_module_type.append([get_color(processed_time_readable, False) + str(queue), str(moduleNum), str(card), str(startTime_readable), str(processed_time_readable), str(path) + get_color(None, False)])

                                else:
                                    printarray2.append([get_color(processed_time_readable, True) + str(queue), str(moduleNum), str(card), str(startTime_readable), str(processed_time_readable), str(path) + get_color(None, True)])
                            array_module_type.sort(lambda x,y: cmp(x[4], y[4]), reverse=True)
                    for e in array_module_type:
                        printarray1.append(e)

                for curr_queue in module_file_array:
                    if curr_queue not in all_queue:
                            printarray3.append([curr_queue, "Not running"])
                    else:
                        if len(list(server.smembers('MODULE_TYPE_'+curr_queue))) == 0:
                            if curr_queue not in no_info_modules:
                                no_info_modules[curr_queue] = int(time.time())
                                printarray3.append([curr_queue, "No data"])
                            else:
                                #If no info since long time, try to kill
                                if args.autokill == 1:
                                    if int(time.time()) - no_info_modules[curr_queue] > args.treshold:
                                        kill_module(curr_queue, None)
                                        no_info_modules[curr_queue] = int(time.time())
                                    printarray3.append([curr_queue, "Stuck or idle, restarting in " + str(abs(args.treshold - (int(time.time()) - no_info_modules[curr_queue]))) + "s"])
                                else:
                                    printarray3.append([curr_queue, "Stuck or idle, restarting disabled"])

                ## FIXME To add:
                ## Button KILL Process using  Curses

                printarray1.sort(key=lambda x: x[0][9:], reverse=False)
                printarray2.sort(key=lambda x: x[0][9:], reverse=False)
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

                printarray4 = []
                for elem in printarrayGlob:
                    if elem is not None:
                        printarray4.append(elem)

                t4 = AsciiTable(printarray4, title="Last actions")
                t4.column_max_width(1)

                legend_array = [["Color", "Meaning"], [Back.RED+Style.BRIGHT+" "*10+Style.RESET_ALL, "Time >=" +str(args.treshold)+Style.RESET_ALL], [Back.MAGENTA+Style.BRIGHT+" "*10+Style.RESET_ALL, "Time >=" +str(args.treshold)+" while idle"+Style.RESET_ALL], [Back.YELLOW+Style.BRIGHT+" "*10+Style.RESET_ALL, "Time >=" +str(args.treshold/2)+Style.RESET_ALL], [Back.GREEN+Style.BRIGHT+" "*10+Style.RESET_ALL, "Time <" +str(args.treshold)]]
                legend = AsciiTable(legend_array, title="Legend")
                legend.column_max_width(1)

                print(legend.table)
                print('\n')
                print(t1.table)
                print('\n')
                print(t2.table)
                print('\n')
                print(t3.table)
                print('\n')
                print(t4.table9)

                if (datetime.datetime.now() - lastTime).total_seconds() > args.refresh*5:
                    lastTime = datetime.datetime.now()
                    cleanRedis()
                #time.sleep(args.refresh)

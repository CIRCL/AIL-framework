#!/usr/bin/env python2
# -*-coding:UTF-8 -*

from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, Label
from asciimatics.effects import Cycle, Print, Stars
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.event import Event
import sys, os
import time, datetime
import argparse, ConfigParser
import json
import redis

 # CONFIG VARIABLES
kill_retry_threshold = 60 #1m
log_filename = "../logs/moduleInfo.log"
command_search_pid = "ps a -o pid,cmd | grep {}"
command_search_name = "ps a -o pid,cmd | grep {}"
command_restart_module = "screen -S \"Script\" -X screen -t \"{}\" bash -c \"./{}.py; read x\""

printarrayGlob = [None]*14
printarrayGlob.insert(0, ["Time", "Module", "PID", "Action"])
lastTimeKillCommand = {}
TABLES = {"running": [("fetching information...",0)], "idle": [("fetching information...",0)], "notRunning": [("fetching information...",0)], "logs": [("No events recorded yet", 0)]}

class CListBox(ListBox):
    def __init__(self, queue_name, *args, **kwargs):
        self.queue_name = queue_name
        super(CListBox, self).__init__(*args, **kwargs)

    def update(self, frame_no):
        self._options = TABLES[self.queue_name]
        ListBox.update(self, frame_no)

class CLabel(Label):
    def __init__(self, label):
        super(Label, self).__init__(None, tab_stop=False)
        # Although this is a label, we don't want it to contribute to the layout
        # tab calculations, so leave internal `_label` value as None.
        self._text = label

    def set_layout(self, x, y, offset, w, h):
        # Do the usual layout work. then recalculate exact x/w values for the
        # rendered button.
        super(Label, self).set_layout(x, y, offset, w, h)
        self._x += max(0, (self._w - self._offset - len(self._text)) // 2)
        self._w = min(self._w, len(self._text))

    def update(self, frame_no):
        (colour, attr, bg) = self._frame.palette["title"]
        self._frame.canvas.print_at(
            self._text, self._x, self._y, colour, attr, bg)

class ListView(Frame):
    # Override standard palette for pop-ups
#        "selected_field":
#            (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLUE),
#        "focus_field":
#            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
#        "selected_focus_field":
#            (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
    def __init__(self, screen):
        super(ListView, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       on_load=self._reload_list,
                                       hover_focus=True)

        self._list_view_run_queue = CListBox(
            "running",
            screen.height // 2,
            [], name="LIST", on_change=self._on_pick)
        self._list_view_idle_queue = CListBox(
            "idle",
            screen.height // 2,
            [], name="LIST", on_change=self._on_pick)
        self._list_view_noRunning = CListBox(
            "notRunning",
            screen.height // 4,
            [], name="LIST", on_change=self._on_pick)
        self._list_view_Log = CListBox(
            "logs",
            screen.height // 4,
            [], name="LIST", on_change=self._on_pick)

        #Running Queues
        layout = Layout([100])
        self.add_layout(layout)
        text_rq = CLabel("Running Queues")
        layout.add_widget(text_rq)
        layout.add_widget(self._list_view_run_queue)
        layout.add_widget(Divider())

        #Idling Queues
        layout2 = Layout([1,1])
        self.add_layout(layout2)
        text_iq = CLabel("Idling Queues")
        layout2.add_widget(text_iq)
        layout2.add_widget(self._list_view_idle_queue, 0)
        #Non Running Queues
        text_nq = CLabel("No Running Queues")
        layout2.add_widget(text_nq, 1)
        layout2.add_widget(self._list_view_noRunning, 1)
        layout2.add_widget(Divider(), 1)
        #Log
        text_l = CLabel("Logs")
        layout2.add_widget(text_l, 1)
        layout2.add_widget(self._list_view_Log, 1)

        self.fix()
        self._on_pick()

    def _on_pick(self):
        return

    def _reload_list(self):
        self._list_view_run_queue = [(time.time(), 123)]

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")


def demo(screen):
    LV = ListView(screen)
    scenes = [
        Scene([LV], -1)
    ]

   # screen.play(scenes)
    screen.set_scenes(scenes)
    time_cooldown = time.time()
    global TABLES
    while True:
        LV._update(None)
        screen.draw_next_frame()
        if time.time() - time_cooldown > 1:
            for key, val in fetchQueueData().iteritems():
                TABLES[key] = val
            screen.refresh()
            time_cooldown = time.time()
        time.sleep(0.02)


def getPid(module):
    p = Popen([command_search_pid.format(module+".py")], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
    for line in p.stdout:
        print line
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
                print flag_pid_valid, 'cleaning', pid, 'in', k
                server.srem(k, pid)
                inst_time = datetime.datetime.fromtimestamp(int(time.time()))
                printarrayGlob.insert(1, [inst_time, moduleName, pid, "Cleared invalid pid in " + k])
                printarrayGlob.pop()
                #time.sleep(5)


def kill_module(module, pid):
    print ''
    print '-> trying to kill module:', module

    if pid is None:
        print 'pid was None'
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
            print pid, 'already killed'
            inst_time = datetime.datetime.fromtimestamp(int(time.time()))
            printarrayGlob.insert(1, [inst_time, module, pid, "Already killed"])
            printarrayGlob.pop()
            return
        time.sleep(1)
        if getPid(module) is None:
            print module, 'has been killed'
            print 'restarting', module, '...'
            p2 = Popen([command_restart_module.format(module, module)], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
            inst_time = datetime.datetime.fromtimestamp(int(time.time()))
            printarrayGlob.insert(1, [inst_time, module, pid, "Killed"])
            printarrayGlob.insert(1, [inst_time, module, "?", "Restarted"])
            printarrayGlob.pop()
            printarrayGlob.pop()

        else:
            print 'killing failed, retrying...'
            inst_time = datetime.datetime.fromtimestamp(int(time.time()))
            printarrayGlob.insert(1, [inst_time, module, pid, "Killing #1 failed."])
            printarrayGlob.pop()

            time.sleep(1)
            os.kill(pid, signal.SIGUSR1)
            time.sleep(1)
            if getPid(module) is None:
                print module, 'has been killed'
                print 'restarting', module, '...'
                p2 = Popen([command_restart_module.format(module, module)], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
                inst_time = datetime.datetime.fromtimestamp(int(time.time()))
                printarrayGlob.insert(1, [inst_time, module, pid, "Killed"])
                printarrayGlob.insert(1, [inst_time, module, "?", "Restarted"])
                printarrayGlob.pop()
                printarrayGlob.pop()
            else:
                print 'killing failed!'
                inst_time = datetime.datetime.fromtimestamp(int(time.time()))
                printarrayGlob.insert(1, [inst_time, module, pid, "Killing failed!"])
                printarrayGlob.pop()
    else:
        print 'Module does not exist'
        inst_time = datetime.datetime.fromtimestamp(int(time.time()))
        printarrayGlob.insert(1, [inst_time, module, pid, "Killing failed, module not found"])
        printarrayGlob.pop()
    #time.sleep(5)
    cleanRedis()




def fetchQueueData():

    all_queue = set()
    printarray1 = []
    printarray2 = []
    printarray3 = []
    for queue, card in server.hgetall("queues").iteritems():
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
                            #log = open(log_filename, 'a')
                            #log.write(json.dumps([queue, card, str(startTime_readable), str(processed_time_readable), path]) + "\n")
                            try:
                                last_kill_try = time.time() - lastTimeKillCommand[moduleNum]
                            except KeyError:
                                last_kill_try = kill_retry_threshold+1
                            if args.autokill == 1 and last_kill_try > kill_retry_threshold :
                                kill_module(queue, int(moduleNum))
    
                        array_module_type.append( (["   ", str(queue), str(moduleNum), str(card), str(startTime_readable), str(processed_time_readable), str(path)], moduleNum) )
    
                    else:
                        printarray2.append( (["   ", str(queue), str(moduleNum), str(processed_time_readable), str(path)], moduleNum) )
                array_module_type.sort(lambda x,y: cmp(x[0][4], y[0][4]), reverse=True)
        for e in array_module_type:
            printarray1.append(e)
    
    for curr_queue in module_file_array:
        if curr_queue not in all_queue:
                printarray3.append( (["   ", curr_queue, "Not running"], len(printarray3)+1) )
        else:
            if len(list(server.smembers('MODULE_TYPE_'+curr_queue))) == 0:
                if curr_queue not in no_info_modules:
                    no_info_modules[curr_queue] = int(time.time())
                    printarray3.append( (["   ", curr_queue, "No data"], len(printarray3)+1) )
                else:
                    #If no info since long time, try to kill
                    if args.autokill == 1:
                        if int(time.time()) - no_info_modules[curr_queue] > args.treshold:
                            kill_module(curr_queue, None)
                            no_info_modules[curr_queue] = int(time.time())
                        printarray3.append( (["   ", curr_queue, "Stuck or idle, restarting in " + str(abs(args.treshold - (int(time.time()) - no_info_modules[curr_queue]))) + "s"], len(printarray3)+1) )
                    else:
                        printarray3.append( (["   ", curr_queue, "Stuck or idle, restarting disabled"], len(printarray3)+1) )
    
    ## FIXME To add:
    ## Button KILL Process using  Curses
    
    printarray1.sort(key=lambda x: x[0], reverse=False)
    printarray2.sort(key=lambda x: x[0], reverse=False)
    printarray1.insert(0,(["   ", "Queue name", "PID", "#", "S Time", "R Time", "Processed element", "CPU", "Mem", "Avg CPU"], 0) )
    printarray2.insert(0,(["   ", "Queue", "PID", "Idle Time", "Last paste hash"], 0) )
    printarray3.insert(0,(["   ", "Queue", "State"], 0) )

    padding_row = [5, 23, 8, 
                        8, 23, 10,
                        45, 6, 6, 8]
    printstring1 = []
    for row in printarray1:
        the_array = row[0]
        the_pid = row[1]
        text=""
        for ite, elem in enumerate(the_array):
            if len(elem) > padding_row[ite]:
                text += "*" + elem[-padding_row[ite]+6:]
                padd_off = " "*5
            else:
                text += elem
                padd_off = " "*0
            text += (padding_row[ite] - len(elem))*" " + padd_off
        printstring1.append( (text, the_pid) )

    padding_row = [5, 23, 8, 
                   12, 45]
    printstring2 = []
    for row in printarray2:
        the_array = row[0]
        the_pid = row[1]
        text=""
        for ite, elem in enumerate(the_array):
            if len(elem) > padding_row[ite]:
                text += "*" + elem[-padding_row[ite]+6:]
                padd_off = " "*5
            else:
                text += elem
                padd_off = " "*0
            text += (padding_row[ite] - len(elem))*" " + padd_off
        printstring2.append( (text, the_pid) )

    padding_row = [5, 23, 35] 
    printstring3 = []
    for row in printarray3:
        the_array = row[0]
        the_pid = row[1]
        text=""
        for ite, elem in enumerate(the_array):
            if len(elem) > padding_row[ite]:
                text += "*" + elem[-padding_row[ite]+6:]
                padd_off = " "*5
            else:
                text += elem
                padd_off = " "*0
            text += (padding_row[ite] - len(elem))*" " + padd_off
        printstring3.append( (text, the_pid) )

    return {"running": printstring1, "idle": printstring2, "notRunning": printstring3}



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
    no_info_modules = {}
    path_allmod = os.path.join(os.environ['AIL_HOME'], 'doc/all_modules.txt')
    with open(path_allmod, 'r') as module_file:
        for line in module_file:
            module_file_array.add(line[:-1])

        #cleanRedis()



    while True:
       Screen.wrapper(demo)
       sys.exit(0)


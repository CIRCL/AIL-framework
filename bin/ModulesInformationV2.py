#!/usr/bin/env python3
# -*-coding:UTF-8 -*

from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, Label
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from asciimatics.event import Event
from asciimatics.event import KeyboardEvent, MouseEvent
import sys, os
import time, datetime
import argparse, configparser
import json
import redis
import psutil
from subprocess import PIPE, Popen
from packages import Paste

 # CONFIG VARIABLES
kill_retry_threshold = 60 #1m
log_filename = "../logs/moduleInfo.log"
command_search_pid = "ps a -o pid,cmd | grep {}"
command_search_name = "ps a -o pid,cmd | grep {}"
command_restart_module = "screen -S \"Script\" -X screen -t \"{}\" bash -c \"./{}.py; read x\""

printarrayLog = [None]*14
lastTimeKillCommand = {}

# Used to pass information through scenes
current_selected_value = 0
current_selected_queue = ""
current_selected_action = ""
current_selected_amount = 0

# Map PID to Queue name (For restart and killing)
PID_NAME_DICO = {}

# Tables containing info for the dashboad
TABLES = {"running": [], "idle": [], "notRunning": [], "logs": [("No events recorded yet", 0)]}
TABLES_TITLES = {"running": "", "idle": "", "notRunning": "", "logs": ""}
TABLES_PADDING = {"running": [12, 23, 8, 8, 23, 10, 55, 11, 11, 12], "idle": [9, 23, 8, 12, 50], "notRunning": [9, 23, 35], "logs": [15, 23, 8, 50]}

# Indicator for the health of a queue (green(0), red(2), yellow(1))
QUEUE_STATUS = {}

# Maintain the state of the CPU objects
CPU_TABLE = {}
CPU_OBJECT_TABLE = {}

# Path of the current paste for a pid
COMPLETE_PASTE_PATH_PER_PID = {}

'''
ASCIIMATICS WIDGETS EXTENSION
'''

# Custom listbox
class CListBox(ListBox):

    def __init__(self, queue_name, *args, **kwargs):
        self.queue_name = queue_name
        super(CListBox, self).__init__(*args, **kwargs)

    def update(self, frame_no):
        self._options = TABLES[self.queue_name]

        self._draw_label()

        # Calculate new visible limits if needed.
        width = self._w - self._offset
        height = self._h
        dx = dy = 0

        # Clear out the existing box content
        (colour, attr, bg) = self._frame.palette["field"]
        for i in range(height):
            self._frame.canvas.print_at(
                " " * width,
                self._x + self._offset + dx,
                self._y + i + dy,
                colour, attr, bg)

        # Don't bother with anything else if there are no options to render.
        if len(self._options) <= 0:
            return

        # Render visible portion of the text.
        self._start_line = max(0, max(self._line - height + 1,
                                      min(self._start_line, self._line)))
        for i, (text, pid) in enumerate(self._options):
            if self._start_line <= i < self._start_line + height:
                colour, attr, bg = self._pick_colours("field", i == self._line)
                self._frame.canvas.print_at(
                    "{:{width}}".format(text, width=width),
                    self._x + self._offset + dx,
                    self._y + i + dy - self._start_line,
                    colour, attr, bg)

                # Pick color depending on queue health
                if self.queue_name == "running":
                    if QUEUE_STATUS[pid] == 2:
                        queueStatus = Screen.COLOUR_RED
                    elif QUEUE_STATUS[pid] == 1:
                        queueStatus = Screen.COLOUR_YELLOW
                    else:
                        queueStatus = Screen.COLOUR_GREEN

                    self._frame.canvas.print_at(" ",
                        self._x + 9 + dx,
                        self._y + i + dy - self._start_line,
                        colour, attr, queueStatus)


    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if len(self._options) > 0 and event.key_code == Screen.KEY_UP:
                # Move up one line in text - use value to trigger on_select.
                self._line = max(0, self._line - 1)
                self._line = min(self._line, len(self._options)-1) #If we move a line cursor from a line that has dissapear
                self.value = self._options[self._line][1]

            elif len(self._options) > 0 and event.key_code == Screen.KEY_DOWN:
                # Move down one line in text - use value to trigger on_select.
                self._line = min(len(self._options) - 1, self._line + 1)
                self.value = self._options[self._line][1]

            elif len(self._options) > 0 and event.key_code in [ord(' '), ord('\n')] :
                global current_selected_value, current_selected_queue
                if self.queue_name == "logs":
                    return event
                current_selected_value = self.value
                current_selected_queue = self.queue_name
                self._frame.save()
                raise NextScene("action_choice")

            # Quit if press q
            elif event.key_code == ord('q'):
                Dashboard._quit()

            else:
                # Ignore any other key press.
                return event

        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            new_event = self._frame.rebase_event(event)
            if event.buttons != 0:
                if (len(self._options) > 0 and
                        self.is_mouse_over(new_event, include_label=False)):
                    # Use property to trigger events.
                    self._line = min(new_event.y - self._y,
                                     len(self._options) - 1)
                    self.value = self._options[self._line][1]
                    # If clicked on button <k>, kill the queue
                    if self._x+2 <= new_event.x < self._x+4:
                        if self.queue_name in ["running", "idle"]:
                            kill_module(PID_NAME_DICO[int(self.value)], self.value)
                        else:
                            restart_module(self.value)

                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event


# Custom label centered in the middle
class CLabel(Label):
    def __init__(self, label, listTitle=False):
        super(Label, self).__init__(None, tab_stop=False)
        # Although this is a label, we don't want it to contribute to the layout
        # tab calculations, so leave internal `_label` value as None.
        self._text = label
        self.listTitle = listTitle
        self._required_height = 1

    def set_layout(self, x, y, offset, w, h):
        # Do the usual layout work. then recalculate exact x/w values for the
        # rendered button.
        super(Label, self).set_layout(x, y, offset, w, h)
        self._x += max(0, (self._w - self._offset - len(self._text)) // 2) if not self.listTitle else 0
        self._w = min(self._w, len(self._text))

    def update(self, frame_no):
        (colour, attr, bg) = self._frame.palette["title"]
        colour = Screen.COLOUR_YELLOW if not self.listTitle else colour
        self._frame.canvas.print_at(
            self._text, self._x, self._y, colour, attr, bg)

'''
END EXTENSION
'''

'''
SCENE DEFINITION
'''

class Dashboard(Frame):
    def __init__(self, screen):
        super(Dashboard, self).__init__(screen,
                                       screen.height,
                                       screen.width,
                                       hover_focus=True,
                                       reduce_cpu=True)

        self._list_view_run_queue = CListBox(
            "running",
            screen.height // 2,
            [], name="LIST")
        self._list_view_idle_queue = CListBox(
            "idle",
            screen.height // 2,
            [], name="LIST")
        self._list_view_noRunning = CListBox(
            "notRunning",
            screen.height // 5,
            [], name="LIST")
        self._list_view_Log = CListBox(
            "logs",
            screen.height // 4,
            [], name="LIST")
        #self._list_view_Log.disabled = True


        #Running Queues
        layout = Layout([100])
        self.add_layout(layout)
        text_rq = CLabel("Running Queues")
        layout.add_widget(text_rq)
        layout.add_widget(CLabel(TABLES_TITLES["running"], listTitle=True))
        layout.add_widget(self._list_view_run_queue)
        layout.add_widget(Divider())

        #Idling Queues
        layout2 = Layout([1,1])
        self.add_layout(layout2)
        text_iq = CLabel("Idling Queues")
        layout2.add_widget(text_iq, 0)
        layout2.add_widget(CLabel(TABLES_TITLES["idle"], listTitle=True), 0)
        layout2.add_widget(self._list_view_idle_queue, 0)
        #Non Running Queues
        text_nq = CLabel("Queues not running")
        layout2.add_widget(text_nq, 1)
        layout2.add_widget(CLabel(TABLES_TITLES["notRunning"], listTitle=True), 1)
        layout2.add_widget(self._list_view_noRunning, 1)
        layout2.add_widget(Divider(), 1)
        #Log
        text_l = CLabel("Logs")
        layout2.add_widget(text_l, 1)
        layout2.add_widget(CLabel(TABLES_TITLES["logs"], listTitle=True), 1)
        layout2.add_widget(self._list_view_Log, 1)

        self.fix()

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

class Confirm(Frame):
    def __init__(self, screen):
        super(Confirm, self).__init__(screen,
                                          screen.height * 1 // 8,
                                          screen.width * 1 // 3,
                                          hover_focus=True,
                                          on_load=self._setValue,
                                          title="Confirm action",
                                          reduce_cpu=True)

        # Create the form for displaying the list of contacts.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        self.label = CLabel("{} module {} {}?")
        layout.add_widget(Label(" "))
        layout.add_widget(self.label)
        layout2 = Layout([1,1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Ok", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 1)

        self.fix()

    def _ok(self):
        global current_selected_value, current_selected_queue, current_selected_action, current_selected_amount
        if current_selected_action == "KILL":
            kill_module(PID_NAME_DICO[int(current_selected_value)], current_selected_value)
        else:
            count = int(current_selected_amount) #Number of queue to start
            if current_selected_queue in ["running", "idle"]:
                restart_module(PID_NAME_DICO[int(current_selected_value)], count)
            else:
                restart_module(current_selected_value, count)

        current_selected_value = 0
        current_selected_amount = 0
        current_selected_action = ""
        self.label._text = "{} module {} {}?"
        self.save()
        raise NextScene("dashboard")

    def _cancel(self):
        global current_selected_value
        current_selected_value = 0
        current_selected_amount = 0
        current_selected_action = ""
        self.label._text = "{} module {} {}?"
        self.save()
        raise NextScene("dashboard")

    def _setValue(self):
        global current_selected_value, current_selected_queue, current_selected_action, current_selected_amount
        if current_selected_queue in ["running", "idle"]:
            action = current_selected_action if current_selected_action == "KILL" else current_selected_action +" "+ str(current_selected_amount) + "x"
            modulename = PID_NAME_DICO[int(current_selected_value)]
            pid = current_selected_value
        else:
            action = current_selected_action + " " + str(current_selected_amount) + "x"
            modulename = current_selected_value
            pid = ""
        self.label._text = self.label._text.format(action, modulename, pid)

class Action_choice(Frame):
    def __init__(self, screen):
        super(Action_choice, self).__init__(screen,
                                          screen.height * 1 // 8,
                                          screen.width * 1 // 2,
                                          hover_focus=True,
                                          on_load=self._setValue,
                                          title="Confirm action",
                                          reduce_cpu=True)

        # Create the form for displaying the list of contacts.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        self.label = CLabel("Choose action on module {} {}")
        layout.add_widget(self.label)
        layout2 = Layout([1,1,1,1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Cancel", self._cancel), 0)
        self._ShowPasteBtn = Button("Show current paste", self._showpaste)
        layout2.add_widget(self._ShowPasteBtn, 1)
        self._killBtn = Button("KILL", self._kill)
        layout2.add_widget(self._killBtn, 2)
        layout2.add_widget(Button("START", self._start), 3)
        layout3 = Layout([1,1,1,1])
        self.add_layout(layout3)
        self.textEdit = Text("Amount", "amount")
        layout3.add_widget(self.textEdit, 3)

        self.fix()

    def _kill(self):
        global current_selected_action
        current_selected_action = "KILL"
        self.label._text = "Choose action on module {} {}"
        self.save()
        raise NextScene("confirm")

    def _start(self):
        global current_selected_action, current_selected_amount
        current_selected_action = "START"
        try:
            count = int(self.textEdit.value)
            count = count if count < 20 else 1
        except Exception:
            count = 1
        current_selected_amount = count
        self.label._text = "Choose action on module {} {}"
        self.save()
        raise NextScene("confirm")


    def _cancel(self):
        global current_selected_value
        current_selected_value = 0
        self.label._text = "Choose action on module {} {}"
        self.save()
        raise NextScene("dashboard")

    def _showpaste(self):
        self.label._text = "Choose action on module {} {}"
        self.save()
        raise NextScene("show_paste")

    def _setValue(self):
        self._killBtn.disabled = False
        self._ShowPasteBtn.disabled = False
        global current_selected_value, current_selected_queue
        if current_selected_queue in ["running", "idle"]:
            modulename = PID_NAME_DICO[int(current_selected_value)]
            pid = current_selected_value
        else:
            self._killBtn.disabled = True
            self._ShowPasteBtn.disabled = True
            modulename = current_selected_value
            pid = ""
        self.label._text = self.label._text.format(modulename, pid)

class Show_paste(Frame):
    def __init__(self, screen):
        super(Show_paste, self).__init__(screen,
                                          screen.height,
                                          screen.width,
                                          hover_focus=True,
                                          on_load=self._setValue,
                                          title="Show current paste",
                                          reduce_cpu=True)

        layout = Layout([100], fill_frame=True)
        self.layout = layout
        self.add_layout(layout)

        self.label_list = []
        self.num_label = 42 # Number of line available for displaying the paste
        for i in range(self.num_label):
            self.label_list += [Label("THE PASTE CONTENT " + str(i))]
            layout.add_widget(self.label_list[i])

        layout2 = Layout([100])
        self.add_layout(layout2)
        layout2.add_widget(Button("Ok", self._ok), 0)
        self.fix()

    def _ok(self):
        global current_selected_value, current_selected_queue, current_selected_action, current_selected_amount
        current_selected_value = 0
        current_selected_amount = 0
        current_selected_action = ""
        self.save()
        raise NextScene("dashboard")

    def _setValue(self):
        try:
            #Verify that the  module have a paste
            if COMPLETE_PASTE_PATH_PER_PID[current_selected_value] is None:
                self.label_list[0]._text = "No paste for this module"
                for i in range(1,self.num_label):
                    self.label_list[i]._text = ""
                return

            paste = Paste.Paste(COMPLETE_PASTE_PATH_PER_PID[current_selected_value])
            old_content = paste.get_p_content()[0:4000] # Limit number of char to be displayed

            #Replace unprintable char by ?
            content = ""
            for i, c in enumerate(old_content):
                if ord(c) > 127: # Used to avoid printing unprintable char
                    content += '?'
                elif c == "\t":  # Replace tab by 4 spaces
                    content += "    "
                else:
                    content += c

            #Print in the correct label, END or more
            to_print = ""
            i = 0
            for line in content.split("\n"):
                if i > self.num_label - 2:
                    break
                self.label_list[i]._text = str(i) + ". " + line.replace("\r","")
                i += 1

            if i > self.num_label - 2:
                self.label_list[i]._text = "- ALL PASTE NOT DISPLAYED -"
                i += 1
            else:
                self.label_list[i]._text = "- END of PASTE -"
                i += 1

            while i<self.num_label: #Clear out remaining lines
                self.label_list[i]._text = ""
                i += 1

        except OSError as e:
            self.label_list[0]._text = "Error during parsing the filepath. Please, check manually"
            self.label_list[1]._text = COMPLETE_PASTE_PATH_PER_PID[current_selected_value]
            for i in range(2,self.num_label):
                self.label_list[i]._text = ""

        except Exception as e:
            if current_selected_value in COMPLETE_PASTE_PATH_PER_PID:
                self.label_list[0]._text = "Error while displaying the paste: " + COMPLETE_PASTE_PATH_PER_PID[current_selected_value]
            else:
                self.label_list[0]._text = "Error Generic exception caught"
            self.label_list[1]._text = str(e)
            for i in range(2,self.num_label):
                self.label_list[i]._text = ""

'''
END SCENES DEFINITION
'''


'''
MANAGE MODULES AND GET INFOS
'''

def getPid(module):
    p = Popen([command_search_pid.format(module+".py")], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
    for line in p.stdout:
        splittedLine = line.split()
        if 'python3' in splittedLine:
            return int(splittedLine[0])
    return None

def clearRedisModuleInfo():
    for k in server.keys("MODULE_*"):
        server.delete(k)
    inst_time = datetime.datetime.fromtimestamp(int(time.time()))
    log(([str(inst_time).split(' ')[1], "*", "-", "Cleared redis module info"], 0))

def cleanRedis():
    for k in server.keys("MODULE_TYPE_*"):
        moduleName = k[12:].split('_')[0]
        for pid in server.smembers(k):
            flag_pid_valid = False
            proc = Popen([command_search_name.format(pid)], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
            try:
                for line in proc.stdout:
                    line = line.decode('utf8')
                    splittedLine = line.split()
                    if ('python3.5' in splittedLine or 'python3' in splittedLine or 'python' in splittedLine):
                        moduleCommand = "./"+moduleName + ".py"
                        moduleCommand2 = moduleName + ".py"
                        if(moduleCommand in splittedLine or moduleCommand2 in splittedLine):
                            flag_pid_valid = True


                if not flag_pid_valid:
                    #print flag_pid_valid, 'cleaning', pid, 'in', k
                    server.srem(k, pid)
                    inst_time = datetime.datetime.fromtimestamp(int(time.time()))
                    log(([str(inst_time).split(' ')[1], moduleName, pid, "Cleared invalid pid in " + (k)], 0))

            #Error due to resize, interrupted sys call
            except IOError as e:
                inst_time = datetime.datetime.fromtimestamp(int(time.time()))
                log(([str(inst_time).split(' ')[1], " - ", " - ", "Cleaning fail due to resize."], 0))


def restart_module(module, count=1):
    for i in range(count):
        p2 = Popen([command_restart_module.format(module, module)], stdin=PIPE, stdout=PIPE, bufsize=1, shell=True)
        time.sleep(0.2)
    inst_time = datetime.datetime.fromtimestamp(int(time.time()))
    log(([str(inst_time).split(' ')[1], module, "?", "Restarted " + str(count) + "x"], 0))


def kill_module(module, pid):
    #print '-> trying to kill module:', module

    if pid is None:
        #print 'pid was None'
        inst_time = datetime.datetime.fromtimestamp(int(time.time()))
        log(([str(inst_time).split(' ')[1], module, pid, "PID was None"], 0))
        pid = getPid(module)
    else: #Verify that the pid is at least in redis
        if server.exists("MODULE_"+module+"_"+str(pid)) == 0:
            return

    lastTimeKillCommand[pid] = int(time.time())
    if pid is not None:
        try:
            p = psutil.Process(int(pid))
            p.terminate()
        except Exception as e:
            #print pid, 'already killed'
            inst_time = datetime.datetime.fromtimestamp(int(time.time()))
            log(([str(inst_time).split(' ')[1], module, pid, "Already killed"], 0))
            return
        time.sleep(0.2)
        if not p.is_running():
            #print module, 'has been killed'
            #print 'restarting', module, '...'
            inst_time = datetime.datetime.fromtimestamp(int(time.time()))
            log(([str(inst_time).split(' ')[1], module, pid, "Killed"], 0))
            #restart_module(module)

        else:
            #print 'killing failed, retrying...'
            inst_time = datetime.datetime.fromtimestamp(int(time.time()))
            log(([str(inst_time).split(' ')[1], module, pid, "Killing #1 failed."], 0))

            p.terminate()
            if not p.is_running():
                #print module, 'has been killed'
                #print 'restarting', module, '...'
                inst_time = datetime.datetime.fromtimestamp(int(time.time()))
                log(([str(inst_time).split(' ')[1], module, pid, "Killed"], 0))
                #restart_module(module)
            else:
                #print 'killing failed!'
                inst_time = datetime.datetime.fromtimestamp(int(time.time()))
                log(([str(inst_time).split(' ')[1], module, pid, "Killing failed!"], 0))
    else:
        #print 'Module does not exist'
        inst_time = datetime.datetime.fromtimestamp(int(time.time()))
        log(([str(inst_time).split(' ')[1], module, pid, "Killing failed, module not found"], 0))
    cleanRedis()


# Fetch the data for all queue
def fetchQueueData():

    all_queue = set()
    printarray_running = []
    printarray_idle = []
    printarray_notrunning = []
    for queue, card in iter(server.hgetall("queues").items()):
        all_queue.add(queue)
        key = "MODULE_" + queue + "_"
        keySet = "MODULE_TYPE_" + queue
        array_module_type = []

        for moduleNum in server.smembers(keySet):
            value = server.get(key + str(moduleNum))
            complete_paste_path = ( server.get(key + str(moduleNum) + "_PATH") )
            if(complete_paste_path is not None):
                complete_paste_path = complete_paste_path
            COMPLETE_PASTE_PATH_PER_PID[moduleNum] = complete_paste_path

            if value is not None:
                timestamp, path = value.split(", ")
                if timestamp is not None and path is not None:
                    # Queue health
                    startTime_readable = datetime.datetime.fromtimestamp(int(timestamp))
                    processed_time_readable = str((datetime.datetime.now() - startTime_readable)).split('.')[0]
                    if ((datetime.datetime.now() - startTime_readable).total_seconds()) > args.treshold:
                        QUEUE_STATUS[moduleNum] = 2
                    elif ((datetime.datetime.now() - startTime_readable).total_seconds()) > args.treshold/2:
                        QUEUE_STATUS[moduleNum] = 1
                    else:
                        QUEUE_STATUS[moduleNum] = 0

                    # Queue contain elements
                    if int(card) > 0:
                        # Queue need to be killed
                        if int((datetime.datetime.now() - startTime_readable).total_seconds()) > args.treshold:
                            log(([str(time.time()), queue, "-", "ST:"+str(timestamp)+" PT:"+str(time.time()-float(timestamp))], 0), True, show_in_board=False)
                            try:
                                last_kill_try = time.time() - lastTimeKillCommand[moduleNum]
                            except KeyError:
                                last_kill_try = kill_retry_threshold+1
                            if args.autokill == 1 and last_kill_try > kill_retry_threshold :
                                kill_module(queue, int(moduleNum))

                        # Create CPU objects
                        try:
                            cpu_percent = CPU_OBJECT_TABLE[int(moduleNum)].cpu_percent()
                            CPU_TABLE[moduleNum].insert(1, cpu_percent)
                            cpu_avg = sum(CPU_TABLE[moduleNum])/len(CPU_TABLE[moduleNum])
                            if len(CPU_TABLE[moduleNum]) > args.refresh*10:
                                CPU_TABLE[moduleNum].pop()

                            mem_percent = CPU_OBJECT_TABLE[int(moduleNum)].memory_percent()
                        except psutil.NoSuchProcess:
                            del CPU_OBJECT_TABLE[int(moduleNum)]
                            del CPU_TABLE[moduleNum]
                            cpu_percent = 0
                            cpu_avg = cpu_percent
                            mem_percent = 0
                        except KeyError:
                            #print('key error2')
                            try:
                                CPU_OBJECT_TABLE[int(moduleNum)] = psutil.Process(int(moduleNum))
                                cpu_percent = CPU_OBJECT_TABLE[int(moduleNum)].cpu_percent()
                                CPU_TABLE[moduleNum] = []
                                cpu_avg = cpu_percent
                                mem_percent = CPU_OBJECT_TABLE[int(moduleNum)].memory_percent()
                            except psutil.NoSuchProcess:
                                cpu_percent = 0
                                cpu_avg = cpu_percent
                                mem_percent = 0

                        array_module_type.append( ([" <K>    [ ]", str(queue), str(moduleNum), str(card), str(startTime_readable),
                                                    str(processed_time_readable), str(path), "{0:.2f}".format(cpu_percent)+"%",
                                                    "{0:.2f}".format(mem_percent)+"%", "{0:.2f}".format(cpu_avg)+"%"], moduleNum) )

                    else:
                        printarray_idle.append( ([" <K>  ", str(queue), str(moduleNum), str(processed_time_readable), str(path)], moduleNum) )

                PID_NAME_DICO[int(moduleNum)] = str(queue)
                #array_module_type.sort(lambda x,y: cmp(x[0][4], y[0][4]), reverse=True) #Sort by num of pastes
        for e in array_module_type:
            printarray_running.append(e)

    for curr_queue in module_file_array:
        if curr_queue not in all_queue: #Module not running by default
                printarray_notrunning.append( ([" <S>  ", curr_queue, "Not running by default"], curr_queue) )
        else: #Module did not process anything yet
            if len(list(server.smembers('MODULE_TYPE_'+curr_queue))) == 0:
                if curr_queue not in no_info_modules:
                    no_info_modules[curr_queue] = int(time.time())
                    printarray_notrunning.append( ([" <S>  ", curr_queue, "No data"], curr_queue) )
                else:
                    #If no info since long time, try to kill
                    if args.autokill == 1:
                        if int(time.time()) - no_info_modules[curr_queue] > args.treshold:
                            kill_module(curr_queue, None)
                            no_info_modules[curr_queue] = int(time.time())
                        printarray_notrunning.append( ([" <S>  ", curr_queue, "Stuck or idle, restarting in " + str(abs(args.treshold - (int(time.time()) - no_info_modules[curr_queue]))) + "s"], curr_queue) )
                    else:
                        printarray_notrunning.append( ([" <S>  ", curr_queue, "Stuck or idle, restarting disabled"], curr_queue) )


    printarray_running.sort(key=lambda x: x[0], reverse=False)
    printarray_idle.sort(key=lambda x: x[0], reverse=False)
    printarray_notrunning.sort(key=lambda x: x[0][1], reverse=False)

    printstring_running = format_string(printarray_running, TABLES_PADDING["running"])
    printstring_idle = format_string(printarray_idle, TABLES_PADDING["idle"])
    printstring_notrunning = format_string(printarray_notrunning, TABLES_PADDING["notRunning"])

    return {"running": printstring_running, "idle": printstring_idle, "notRunning": printstring_notrunning}

# Format the input string with its related padding to have collumn like text in CListBox
def format_string(tab, padding_row):
    printstring = []
    for row in tab:
        if row is None:
            continue
        the_array = row[0]
        the_pid = row[1]

        text=""
        for ite, elem in enumerate(the_array):

            if elem is not None and type(elem) is str:
                if len(elem) > padding_row[ite]:
                    text += "*" + elem[-padding_row[ite]+6:]
                    padd_off = " "*5
                else:
                    text += elem
                    padd_off = " "*0
                text += (padding_row[ite] - len(elem))*" " + padd_off

        printstring.append( (text, the_pid) )
    return printstring

def log(data, write_on_disk=False, show_in_board=True):
    if show_in_board:
        printarrayLog.insert(0, data)
        printarrayLog.pop()
    if write_on_disk:
        with open(log_filename, 'a') as log:
            log.write(json.dumps(data[0]) + "\n")

'''
END MANAGE
'''

def demo(screen):
    dashboard = Dashboard(screen)
    confirm = Confirm(screen)
    action_choice = Action_choice(screen)
    show_paste = Show_paste(screen)
    scenes = [
        Scene([dashboard], -1, name="dashboard"),
        Scene([action_choice], -1, name="action_choice"),
        Scene([confirm], -1, name="confirm"),
        Scene([show_paste], -1, name="show_paste"),
    ]


    screen.set_scenes(scenes)
    time_cooldown = time.time() # Cooldown before refresh
    global TABLES
    while True:
        #Stop on resize
        if screen.has_resized():
            screen._scenes[screen._scene_index].exit()
            raise ResizeScreenError("Screen resized", screen._scenes[screen._scene_index])

        if time.time() - time_cooldown > args.refresh:
            cleanRedis()
            for key, val in iter(fetchQueueData().items()): #fetch data and put it into the tables
                TABLES[key] = val
            TABLES["logs"] = format_string(printarrayLog, TABLES_PADDING["logs"])

            #refresh dashboad only if the scene is active (no value selected)
            if current_selected_value == 0:
                dashboard._update(None)
                screen.refresh()
            time_cooldown = time.time()
        screen.draw_next_frame()
        time.sleep(0.02) #time between screen refresh (For UI navigation, not data actualisation)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Show info concerning running modules and log suspected stucked modules. May be use to automatically kill and restart stucked one.')
    parser.add_argument('-r', '--refresh', type=int, required=False, default=5, help='Refresh rate')
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

    try:
        with open(path_allmod, 'r') as module_file:
            for line in module_file:
                module_file_array.add(line[:-1])
    except IOError as e:
        if e.errno == 2: #module_file not found, creating a new one
            print(path_allmod + " not found.\nCreating a new one.")
            os.system("./../doc/generate_modules_data_flow_graph.sh")
            with open(path_allmod, 'r') as module_file:
                for line in module_file:
                    module_file_array.add(line[:-1])
    cleanRedis()


    TABLES_TITLES["running"] = format_string([([" Action", "Queue name", "PID", "#", "S Time", "R Time", "Processed element", "CPU %", "Mem %", "Avg CPU%"],0)], TABLES_PADDING["running"])[0][0]
    TABLES_TITLES["idle"] = format_string([([" Action", "Queue", "PID", "Idle Time", "Last paste hash"],0)], TABLES_PADDING["idle"])[0][0]
    TABLES_TITLES["notRunning"] = format_string([([" Action", "Queue", "State"],0)], TABLES_PADDING["notRunning"])[0][0]
    TABLES_TITLES["logs"] = format_string([(["Time", "Module", "PID", "Info"],0)], TABLES_PADDING["logs"])[0][0]

    try:
        input("Press < ENTER > to launch the manager...")
    except SyntaxError:
        pass

    last_scene = None
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError as e:
            pass
        except StopApplication:
            sys.exit(0)

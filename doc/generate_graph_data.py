#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import os

content = ""
modules = {}
all_modules = []
curr_module = ""
streamingPub = {}
streamingSub = {}

path = os.path.join(os.environ['AIL_BIN'], 'packages/modules.cfg')
path2 = os.path.join(os.environ['AIL_HOME'], 'doc/all_modules.txt')
with open(path, 'r') as f:
    for line in f:
        if line[0] != '#':
            if line[0] == '[':
                curr_name = line.replace('[','').replace(']','').replace('\n', '').replace(' ', '')
                all_modules.append(curr_name)
                modules[curr_name] = {'sub': [], 'pub': []}
                curr_module = curr_name
            elif curr_module != "": # searching for sub or pub
                if line.startswith("subscribe"):
                    curr_subscribers = [w for w in line.replace('\n', '').replace(' ', '').split('=')[1].split(',')]
                    modules[curr_module]['sub'] = curr_subscribers
                    for sub in curr_subscribers:
                        streamingSub[sub] = curr_module

                elif line.startswith("publish"):
                    curr_publishers = [w for w in line.replace('\n', '').replace(' ', '').split('=')[1].split(',')]
                    modules[curr_module]['pub'] = curr_publishers
                    for pub in curr_publishers:
                        streamingPub[pub] = curr_module
                else:
                    continue

    output_set_graph = set()
    with open(path2, 'w') as f2:
        for e in all_modules:
            f2.write(e+"\n")

    for module in modules.keys():
        for stream_in in modules[module]['sub']:
            if stream_in not in streamingPub.keys():
                output_set_graph.add("\"" + stream_in + "\" [color=darkorange1] ;\n")
                output_set_graph.add("\"" + stream_in + "\"" + "->" + module + ";\n")
            else:
                output_set_graph.add("\"" + streamingPub[stream_in] + "\"" + "->" + module + ";\n")

        for stream_out in modules[module]['pub']:
            if stream_out not in streamingSub.keys():
                output_set_graph.add("\"" + stream_out + "\" [color=darkorange1] ;\n")
                output_set_graph.add("\"" + stream_out + "\"" + "->" + module + ";\n")
            else:
                output_set_graph.add("\"" + module + "\"" + "->" + streamingSub[stream_out] + ";\n")


    output_text_graph = ""
    output_text_graph += "digraph unix {\n"\
                              "graph [pad=\"0.5\"];\n"\
                              "size=\"25,25\";\n"\
                              "node [color=lightblue2, style=filled];\n"

    for elem in output_set_graph:
        output_text_graph += elem

    output_text_graph += "}"
    print output_text_graph

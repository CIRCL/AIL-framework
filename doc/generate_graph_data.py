#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import argparse

def main():

    content = ""
    modules = {}
    all_modules = []
    curr_module = ""
    streamingPub = {}
    streamingSub = {}

    path = os.path.join(os.environ['AIL_BIN'], 'packages/modules.cfg') # path to module config file
    path2 = os.path.join(os.environ['AIL_HOME'], 'doc/all_modules.txt') # path and name of the output file, this file contain a list off all modules


    parser = argparse.ArgumentParser(
        description='''This script is a part of the Analysis Information Leak
        framework. It create a graph that represent the flow between modules".''',
        epilog='Example: ./generate_graph_data.py 0')

    parser.add_argument('type', type=int, default=0,
                        help='''The graph type (default 0),
                        0: module graph,
                        1: data graph''',
                        choices=[0, 1], action='store')

    parser.add_argument('spline', type=str, default="ortho",
                        help='''The graph splines type, spline:default , ortho: orthogonal''',
                        choices=["ortho", "spline"], action='store')

    args = parser.parse_args()

    with open(path, 'r') as f:

        # get all modules, subscriber and publisher for each module
        for line in f:
            if line[0] != '#':
                # module name
                if line[0] == '[':
                    curr_name = line.replace('[','').replace(']','').replace('\n', '').replace(' ', '')
                    all_modules.append(curr_name)
                    modules[curr_name] = {'sub': [], 'pub': []}
                    curr_module = curr_name
                elif curr_module != "": # searching for sub or pub
                    # subscriber list
                    if line.startswith("subscribe"):
                        curr_subscribers = [w for w in line.replace('\n', '').replace(' ', '').split('=')[1].split(',')]
                        modules[curr_module]['sub'] = curr_subscribers
                        for sub in curr_subscribers:
                            streamingSub[sub] = curr_module

                    # publisher list
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

        output_text_graph = ""

        # flow between modules
        if args.type == 0:

            for module in modules.keys():
                for stream_in in modules[module]['sub']:
                    if stream_in not in streamingPub.keys():
                        output_set_graph.add("\"" + stream_in + "\" [color=darkorange1] ;\n")
                        output_set_graph.add("\"" + stream_in + "\"" + "->" + module + ";\n")
                    else:
                        output_set_graph.add("\"" + streamingPub[stream_in] + "\"" + "->" + module + ";\n")

                for stream_out in modules[module]['pub']:
                    if stream_out not in streamingSub.keys():
                        #output_set_graph.add("\"" + stream_out + "\" [color=darkorange1] ;\n")
                        output_set_graph.add("\"" + module + "\"" + "->" + stream_out + ";\n")
                    else:
                        output_set_graph.add("\"" + module + "\"" + "->" + streamingSub[stream_out] + ";\n")

            # graph head
            output_text_graph += "digraph unix {\n"
            output_text_graph +=  "graph [pad=\"0.5\"];\n"
            output_text_graph += "size=\"25,25\";\n"
            output_text_graph += "splines="
            output_text_graph += args.spline
            output_text_graph += ";\n"
            output_text_graph += "node [color=lightblue2, style=filled];\n"


        # flow between data
        if args.type == 1:

            for module in modules.keys():
                for stream_in in modules[module]['sub']:
                    for stream_out in modules[module]['pub']:

                        if stream_in not in streamingPub.keys():
                            output_set_graph.add("\"" + stream_in + "\" [color=darkorange1] ;\n")

                        output_set_graph.add("\"" + stream_in + "\"" + "->" + stream_out + ";\n")

            # graph head
            output_text_graph += "digraph unix {\n"
            output_text_graph += "graph [pad=\"0.5\"];\n"
            output_text_graph += "size=\"25,25\";\n"
            output_text_graph += "splines="
            output_text_graph += args.spline
            output_text_graph += ";\n"
            output_text_graph += "node [color=tan, style=filled];\n"



        # create final txt graph
        for elem in output_set_graph:
            output_text_graph += elem

        output_text_graph += "}"
        print(output_text_graph)

if __name__ == "__main__":
    main()

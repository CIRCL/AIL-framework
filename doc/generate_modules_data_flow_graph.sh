#!/bin/bash

python generate_graph_data.py | dot -T png -o module-data-flow.png

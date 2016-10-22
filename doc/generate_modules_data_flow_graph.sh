#!/bin/bash

python $AIL_HOME/doc/generate_graph_data.py | dot -T png -o $AIL_HOME/doc/module-data-flow.png

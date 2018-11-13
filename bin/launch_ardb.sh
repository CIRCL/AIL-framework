#!/bin/bash

GREEN="\\033[1;32m"
DEFAULT="\\033[0;39m"
RED="\\033[1;31m"
ROSE="\\033[1;35m"
BLUE="\\033[1;34m"
WHITE="\\033[0;02m"
YELLOW="\\033[1;33m"
CYAN="\\033[1;36m"

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;

conf_dir="${AIL_HOME}/configs/"

screen -dmS "ARDB_AIL"
sleep 0.1
echo -e $GREEN"\t* Launching ARDB servers"$DEFAULT

sleep 0.1
screen -S "ARDB_AIL" -X screen -t "6382" bash -c 'cd '${AIL_HOME}'; ardb-server '$conf_dir'6382.conf ; read x'

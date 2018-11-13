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

flag_ardb=0
redis_dir=${AIL_HOME}/redis/src/
sleep 0.2
bash -c $redis_dir'redis-cli -p 6382 PING | grep "PONG" &> /dev/null'
if [ ! $? == 0 ]; then
   echo -e $RED"\t6382 ARDB not ready"$DEFAULT
   flag_ardb=1
fi

if [ $flag_ardb == 0 ]; then
    exit 0
else
    exit 1
fi

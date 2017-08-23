#!/bin/bash

set -e
set -x

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_REDIS" ] && echo "Needs the env var AIL_REDIS. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_LEVELDB" ] && echo "Needs the env var AIL_LEVELDB. Run the script from the virtual environment." && exit 1;

conf_dir="${AIL_HOME}/configs/"

screen -dmS "Redis"
sleep 0.1
echo -e $GREEN"\t* Launching Redis servers"$DEFAULT
screen -S "Redis" -X screen -t "6379" bash -c '../redis/src/redis-server '$conf_dir'6379.conf ; read x'
sleep 0.1
screen -S "Redis" -X screen -t "6380" bash -c '../redis/src/redis-server '$conf_dir'6380.conf ; read x'
sleep 0.1
screen -S "Redis" -X screen -t "6381" bash -c '../redis/src/redis-server '$conf_dir'6381.conf ; read x'

# For Words and curves
sleep 0.1
screen -S "Redis" -X screen -t "6382" bash -c '../redis/src/redis-server '$conf_dir'6382.conf ; read x'

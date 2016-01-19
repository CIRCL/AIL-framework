#!/bin/bash

set -e
set -x

conf_dir="${AIL_HOME}/configs/"

screen -dmS "Redis"
sleep 0.1
echo -e $GREEN"\t* Launching Redis servers"$DEFAULT
screen -S "Redis" -X screen -t "6379" bash -c 'redis-server '$conf_dir'6379.conf ; read x'
sleep 0.1
screen -S "Redis" -X screen -t "6380" bash -c 'redis-server '$conf_dir'6380.conf ; read x'
sleep 0.1
screen -S "Redis" -X screen -t "6381" bash -c 'redis-server '$conf_dir'6381.conf ; read x'


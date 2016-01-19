#!/bin/bash

set -e
set -x

screen -dmS "Logging"
sleep 0.1
echo -e $GREEN"\t* Launching logging process"$DEFAULT
screen -S "Logging" -X screen -t "LogQueue" bash -c 'log_subscriber -p 6380 -c Queuing -l ../logs/; read x'
sleep 0.1
screen -S "Logging" -X screen -t "LogScript" bash -c 'log_subscriber -p 6380 -c Script -l ../logs/; read x'


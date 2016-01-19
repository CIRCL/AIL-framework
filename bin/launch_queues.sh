#!/bin/bash

set -e
set -x

screen -dmS "Queue"
sleep 0.1

echo -e $GREEN"\t* Launching all the queues"$DEFAULT
screen -S "Queue" -X screen -t "Queues" bash -c './launch_queues.py; read x'


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

flag_redis=0
redis_dir=${AIL_HOME}/redis/src/
bash -c $redis_dir'redis-cli -p 6379 PING | grep "PONG" &> /dev/null'
if [ ! $? == 0 ]; then
   echo -e $RED"\t6379 not ready"$DEFAULT
   flag_redis=1
fi
sleep 0.1
bash -c $redis_dir'redis-cli -p 6380 PING | grep "PONG" &> /dev/null'
if [ ! $? == 0 ]; then
   echo -e $RED"\t6380 not ready"$DEFAULT
   flag_redis=1
fi
sleep 0.1
bash -c $redis_dir'redis-cli -p 6381 PING | grep "PONG" &> /dev/null'
if [ ! $? == 0 ]; then
   echo -e $RED"\t6381 not ready"$DEFAULT
   flag_redis=1
fi
sleep 0.1

if [ $flag_redis == 0 ]; then
    exit 0
else
    exit 1
fi

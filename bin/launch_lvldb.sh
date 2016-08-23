#!/bin/bash

set -e
set -x

lvdbhost='127.0.0.1'
lvdbdir="${AIL_HOME}/LEVEL_DB_DATA/"
db1_y='2013'
db2_y='2014'
db3_y='2016'
db4_y='3016'
nb_db=13

screen -dmS "LevelDB"
sleep 0.1
echo -e $GREEN"\t* Launching Levels DB servers"$DEFAULT
sleep 0.1
screen -S "LevelDB" -X screen -t "2016" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2016/ -P '$db3_y' -M '$nb_db'; read x'

# For Curve
sleep 0.1
screen -S "LevelDB" -X screen -t "3016" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'3016/ -P '$db4_y' -M '$nb_db'; read x'


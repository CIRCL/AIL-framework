#!/bin/bash

set -e
set -x

lvdbhost='127.0.0.1'
lvdbdir="${AIL_HOME}/LEVEL_DB_DATA/"
db1_y='2013'
db2_y='2014'
db2_y='2015'
db2_y='2016'
nb_db=13

screen -dmS "LevelDB"
sleep 0.1
echo -e $GREEN"\t* Launching Levels DB servers"$DEFAULT
#Add lines here with appropriates options.
screen -S "LevelDB" -X screen -t "2013" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2013/ -P '$db1_y' -M '$nb_db'; read x'
sleep 0.1
screen -S "LevelDB" -X screen -t "2014" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2014/ -P '$db2_y' -M '$nb_db'; read x'
sleep 0.1
screen -S "LevelDB" -X screen -t "2015" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2015/ -P '$db2_y' -M '$nb_db'; read x'
sleep 0.1
screen -S "LevelDB" -X screen -t "2016" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2016/ -P '$db2_y' -M '$nb_db'; read x'


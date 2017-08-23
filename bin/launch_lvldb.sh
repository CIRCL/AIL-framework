#!/bin/bash

set -e
set -x

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_REDIS" ] && echo "Needs the env var AIL_REDIS. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_LEVELDB" ] && echo "Needs the env var AIL_LEVELDB. Run the script from the virtual environment." && exit 1;

lvdbhost='127.0.0.1'
lvdbdir="${AIL_HOME}/LEVEL_DB_DATA/"
nb_db=13

db_y=`date +%Y`
#Verify that a dir with the correct year exists, create it otherwise
if [ ! -d "$lvdbdir$db_y" ]; then
    mkdir -p "$db_y"
fi

screen -dmS "LevelDB"
sleep 0.1
echo -e $GREEN"\t* Launching Levels DB servers"$DEFAULT

#Launch a DB for each dir
for pathDir in $lvdbdir*/ ; do
    yDir=$(basename "$pathDir")
    sleep 0.1
    screen -S "LevelDB" -X screen -t "$yDir" bash -c 'redis-leveldb -H '$lvdbhost' -D '$pathDir'/ -P '$yDir' -M '$nb_db'; read x'
done

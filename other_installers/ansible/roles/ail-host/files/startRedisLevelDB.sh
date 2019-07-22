#!/bin/bash

numberOfDBs=2
currentYear=`/bin/date +%Y`
# -1 because the last process has to be spawned in foreground
let "untilYearLoop = currentYear - 1"
let "startYear = untilYearLoop-numberOfDBs"

for year in $(seq $startYear $untilYearLoop); do
    mkdir -p /opt/AIL-framework/LEVEL_DB_DATA/$year
    /opt/redis-leveldb/redis-leveldb -d -H 127.0.0.1 -D /opt/AIL-framework/LEVEL_DB_DATA/$year -P $year -M 13 &
    done

# Spawn the last instance
mkdir -p /opt/AIL-framework/LEVEL_DB_DATA/2018
/opt/redis-leveldb/redis-leveldb -H 127.0.0.1 -D /opt/AIL-framework/LEVEL_DB_DATA/$currentYear -P $currentYear -M 13


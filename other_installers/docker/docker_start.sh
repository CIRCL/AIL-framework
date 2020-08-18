#!/bin/bash
signalListener() {
    "$@" &
    pid="$!"
    trap "echo 'Stopping'; kill -SIGTERM $pid" SIGINT SIGTERM

    while kill -0 $pid > /dev/null 2>&1; do
        wait
    done
}


source ./AILENV/bin/activate
cd bin
./LAUNCH.sh -l
./LAUNCH.sh -c
./LAUNCH.sh -f

signalListener tail -f /dev/null $@

./LAUNCH.sh -k

#!/bin/bash

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_REDIS" ] && echo "Needs the env var AIL_REDIS. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_ARDB" ] && echo "Needs the env var AIL_ARDB. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_BIN" ] && echo "Needs the env var AIL_ARDB. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_FLASK" ] && echo "Needs the env var AIL_FLASK. Run the script from the virtual environment." && exit 1;

export PATH=$AIL_HOME:$PATH
export PATH=$AIL_REDIS:$PATH
export PATH=$AIL_ARDB:$PATH
export PATH=$AIL_BIN:$PATH
export PATH=$AIL_FLASK:$PATH

echo "Killing all screens ..."
bash -c "bash ${AIL_BIN}/LAUNCH.sh -k"
echo ""
echo "Starting ARDB ..."
bash -c "bash ${AIL_BIN}/launch_ardb.sh"

flag_ardb=true
while $flag_ardb; do
    sleep 1
    bash -c "bash ${AIL_BIN}/check_ardb.sh"
    if [ $? == 0 ]; then
        flag_ardb=false
    else
        echo "ARDB not available, waiting 5s before retry"
        sleep 5
    fi
done

echo ""
echo "Fixing ARDB ..."
echo ""
bash -c "python ${AIL_HOME}/update/v1.5/Update.py"

echo "Shutting down ARDB ..."
bash -c "bash ${AIL_BIN}/LAUNCH.sh -k"

echo ""

exit 0

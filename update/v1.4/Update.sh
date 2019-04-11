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

echo ""
bash -c "bash ${AIL_HOME}/update/bin/Update_Redis.sh"
#bash -c "bash ${AIL_HOME}/update/bin/Update_ARDB.sh"

echo ""
echo "Fixing ARDB ..."
echo ""
bash -c "unbuffer python ${AIL_HOME}/update/v1.5/Update.py"

echo "Shutting down ARDB ..."
bash -c "bash ${AIL_BIN}/LAUNCH.sh -k"

echo ""

exit 0

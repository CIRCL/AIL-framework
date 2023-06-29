#!/bin/bash

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_REDIS" ] && echo "Needs the env var AIL_REDIS. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_BIN" ] && echo "Needs the env var AIL_BIN. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_FLASK" ] && echo "Needs the env var AIL_FLASK. Run the script from the virtual environment." && exit 1;

export PATH=$AIL_HOME:$PATH
export PATH=$AIL_REDIS:$PATH
export PATH=$AIL_BIN:$PATH
export PATH=$AIL_FLASK:$PATH

echo "Killing all screens ..."
bash -c "bash ${AIL_BIN}/LAUNCH.sh -k"
echo ""
echo "Updating Redis ..."
pushd $AIL_HOME/redis
git pull || exit 1
git checkout 5.0 || exit 1
make || exit 1
popd
echo "Redis Updated"
echo ""

exit 0

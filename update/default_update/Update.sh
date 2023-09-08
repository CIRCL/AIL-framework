#!/bin/bash

if [ -z "$1" ]
  then
    echo "No tags version supplied"
fi

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_REDIS" ] && echo "Needs the env var AIL_REDIS. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_KVROCKS" ] && echo "Needs the env var AIL_KVROCKS. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_BIN" ] && echo "Needs the env var AIL_BIN. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_FLASK" ] && echo "Needs the env var AIL_FLASK. Run the script from the virtual environment." && exit 1;

export PATH=$AIL_HOME:$PATH
export PATH=$AIL_REDIS:$PATH
export PATH=AIL_KVROCKS:$PATH
export PATH=$AIL_BIN:$PATH
export PATH=$AIL_FLASK:$PATH

GREEN="\\033[1;32m"
DEFAULT="\\033[0;39m"

echo -e $GREEN"Shutting down AIL Script ..."$DEFAULT
bash ${AIL_BIN}/LAUNCH.sh -ks
wait

echo ""
bash ${AIL_BIN}/LAUNCH.sh -lkv
wait

echo ""
echo -e $GREEN"Updating AIL VERSION ..."$DEFAULT
echo ""
python ${AIL_HOME}/update/default_update/Update.py "-t $1"
wait
echo ""
echo ""

echo ""
echo -e $GREEN"Killing Script ..."$DEFAULT
bash ${AIL_BIN}/LAUNCH.sh -ks
wait

echo ""
echo -e $GREEN"Update thirdparty ..."$DEFAULT
bash ${AIL_BIN}/LAUNCH.sh -t
wait


echo ""

exit 0

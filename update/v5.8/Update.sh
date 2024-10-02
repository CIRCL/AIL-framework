#!/bin/bash

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_REDIS" ] && echo "Needs the env var AIL_REDIS. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_BIN" ] && echo "Needs the env var AIL_ARDB. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_FLASK" ] && echo "Needs the env var AIL_FLASK. Run the script from the virtual environment." && exit 1;

export PATH=$AIL_HOME:$PATH
export PATH=$AIL_REDIS:$PATH
export PATH=$AIL_BIN:$PATH
export PATH=$AIL_FLASK:$PATH

GREEN="\\033[1;32m"
DEFAULT="\\033[0;39m"

echo -e $GREEN"Shutting down AIL ..."$DEFAULT
bash ${AIL_BIN}/LAUNCH.sh -ks
wait

# Install LIB
sudo apt-get install python3-opencv
sudo apt-get install libzbar0


# SUBMODULES #
git submodule update

bash ${AIL_BIN}/LAUNCH.sh -lrv
bash ${AIL_BIN}/LAUNCH.sh -lkv

echo ""
echo -e $GREEN"Updating python packages ..."$DEFAULT
echo ""
pip install -U pyzbar
pip install -U qreader

echo ""
echo -e $GREEN"Updating AIL VERSION ..."$DEFAULT
echo ""
python ${AIL_HOME}/update/v5.8/Update.py
wait
echo ""
echo ""

exit 0

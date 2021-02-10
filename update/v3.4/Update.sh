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

GREEN="\\033[1;32m"
DEFAULT="\\033[0;39m"

echo -e $GREEN"Shutting down AIL ..."$DEFAULT
bash ${AIL_BIN}/LAUNCH.sh -ks
wait

# bash ${AIL_BIN}/LAUNCH.sh -ldbv &
# wait
# echo ""

# SUBMODULES #
git submodule update

# echo ""
# echo -e $GREEN"installing KVORCKS ..."$DEFAULT
# cd ${AIL_HOME}
# test ! -d kvrocks/ && git clone https://github.com/bitleak/kvrocks.git
# pushd kvrocks/
# make -j4
# popd

echo -e $GREEN"Installing html2text ..."$DEFAULT
pip3 install pycld3

echo ""
echo -e $GREEN"Updating AIL VERSION ..."$DEFAULT
echo ""
python ${AIL_HOME}/update/v3.4/Update.py
wait
echo ""
echo ""


echo ""
echo -e $GREEN"Shutting down ARDB ..."$DEFAULT
bash ${AIL_BIN}/LAUNCH.sh -ks
wait

exit 0

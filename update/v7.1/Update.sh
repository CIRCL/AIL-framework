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

# SUBMODULES #
git submodule update

bash ${AIL_BIN}/LAUNCH.sh -lrv
bash ${AIL_BIN}/LAUNCH.sh -lkv

echo -e $GREEN"Updating pyfaup-rs."$DEFAULT
pip install -U 'pyfaup-rs>=0.4.18'

echo -e $GREEN"Installing tempolocus."$DEFAULT
pip install -U 'tempolocus>=1.0.0'

echo -e $GREEN"Installing imagehash."$DEFAULT
pip install -U 'imagehash>=4.3.0' || exit 1

echo -e $GREEN"Installing photo-dna-rs."$DEFAULT
pip install -U 'photo-dna-rs>=0.1.0' || exit 1

echo ""
echo -e $GREEN"Updating AIL VERSION ..."$DEFAULT
echo ""
python ${AIL_HOME}/update/v7.1/Update.py
wait
echo ""
echo ""

exit 0

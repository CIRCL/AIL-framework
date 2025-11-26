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

echo -e $GREEN"Installing python pymupdf..."$DEFAULT
pip install -U pymupdf

echo -e $GREEN"Installing python pymupdf4llm..."$DEFAULT
pip install -U pymupdf4llm

echo -e $GREEN"Updating python Lexilang..."$DEFAULT
pip uninstall -y lexilang
pip install -U git+https://github.com/ail-project/LexiLang

echo -e $GREEN"Updating python pyail."$DEFAULT
pip install -U pyail

echo -e $GREEN"Installing pyfaup-rs."$DEFAULT
pip install -U pyfaup-rs

echo ""
echo -e $GREEN"Updating AIL VERSION ..."$DEFAULT
echo ""
python ${AIL_HOME}/update/v6.6/Update.py
wait
echo ""
echo ""

exit 0

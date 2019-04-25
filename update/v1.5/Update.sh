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
bash ${AIL_BIN}/LAUNCH.sh -k &
wait

echo ""
bash -c "bash ${AIL_HOME}/update/bin/Update_Redis.sh"
#bash -c "bash ${AIL_HOME}/update/bin/Update_ARDB.sh"

echo ""
echo -e $GREEN"Update DomainClassifier"$DEFAULT
echo ""
pip3 install --upgrade --force-reinstall git+https://github.com/D4-project/BGP-Ranking.git/@28013297efb039d2ebbce96ee2d89493f6ae56b0#subdirectory=client&egg=pybgpranking
pip3 install --upgrade --force-reinstall git+https://github.com/adulau/DomainClassifier.git
wait
echo ""

echo ""
echo -e $GREEN"Update Web thirdparty"$DEFAULT
echo ""
bash -c "(cd ${AIL_FLASK}; ./update_thirdparty.sh &)"
wait
echo ""

bash ${AIL_BIN}LAUNCH.sh -lav &
wait
echo ""

echo ""
echo -e $GREEN"Fixing ARDB ..."$DEFAULT
echo ""
python ${AIL_HOME}/update/v1.5/Update.py &
wait
echo ""
echo ""

echo ""
echo -e $GREEN"Shutting down ARDB ..."$DEFAULT
bash ${AIL_BIN}/LAUNCH.sh -k &
wait

echo ""

exit 0

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
echo -e $GREEN"Update DomainClassifier"$DEFAULT
echo ""

cd $AIL_HOME
git clone https://github.com/kazu-yamamoto/pgpdump.git
cd pgpdump
./configure
make
sudo make install
wait
echo ""

echo ""
echo -e $GREEN"Update requirement"$DEFAULT
echo ""
pip3 install beautifulsoup4

bash ${AIL_BIN}LAUNCH.sh -lav &
wait
echo ""

echo ""
echo -e $GREEN"Updating AIL VERSION ..."$DEFAULT
echo ""
python ${AIL_HOME}/update/v1.7/Update.py &
wait
echo ""
echo ""

echo ""
echo -e $GREEN"Shutting down ARDB ..."$DEFAULT
bash ${AIL_BIN}/LAUNCH.sh -k &
wait

echo ""
echo -e $GREEN"Update thirdparty ..."$DEFAULT
bash ${AIL_BIN}/LAUNCH.sh -t &
wait


echo ""

exit 0

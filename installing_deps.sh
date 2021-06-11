#!/bin/bash

# halt on errors
set -e

## bash debug mode togle below
#set -x

sudo apt-get update

sudo apt-get install python3-pip virtualenv python3-dev python3-tk libfreetype6-dev \
    screen g++ python-tk unzip libsnappy-dev cmake -qq

#Needed for downloading jemalloc
sudo apt-get install wget -qq

#optional tor install
sudo apt-get install tor -qq

#Needed for bloom filters
sudo apt-get install libssl-dev libfreetype6-dev python-numpy -qq

#pyMISP
#sudo apt-get -y install python3-pip

# DNS deps
sudo apt-get install libadns1 libadns1-dev -qq

#Needed for redis-lvlDB
sudo apt-get install libev-dev libgmp-dev -qq

#Need for generate-data-flow graph
sudo apt-get install graphviz -qq

# install nosetests
sudo apt-get install python3-nose -qq

# ssdeep
sudo apt-get install libfuzzy-dev -qq
sudo apt-get install build-essential libffi-dev automake autoconf libtool -qq

# sflock, gz requirement
sudo apt-get install p7zip-full -qq

# SUBMODULES #
git submodule init
git submodule update

# REDIS #
test ! -d redis/ && git clone https://github.com/antirez/redis.git
pushd redis/
git checkout 5.0
make
popd

# Faup
test ! -d faup/ && git clone https://github.com/stricaud/faup.git
pushd faup/
test ! -d build && mkdir build
cd build
cmake .. && make
sudo make install
echo '/usr/local/lib' | sudo tee -a /etc/ld.so.conf.d/faup.conf
sudo ldconfig
popd

# tlsh
test ! -d tlsh && git clone https://github.com/trendmicro/tlsh.git
pushd tlsh/
./make.sh
pushd build/release/
sudo make install
sudo ldconfig
popd
popd

# pgpdump
test ! -d pgpdump && git clone https://github.com/kazu-yamamoto/pgpdump.git
pushd pgpdump/
./configure
make
sudo make install
popd

# ARDB #
test ! -d ardb/ && git clone https://github.com/ail-project/ardb.git
pushd ardb/
make
popd

# KVROCKS #
# test ! -d kvrocks/ && git clone https://github.com/bitleak/kvrocks.git
# pushd kvrocks/
# make -j4
# popd

# Config File
if [ ! -f configs/core.cfg ]; then
    cp configs/core.cfg.sample configs/core.cfg
fi

# create AILENV + intall python packages
./install_virtualenv.sh

# force virtualenv activation
if [ -z "$VIRTUAL_ENV" ]; then
    . ./AILENV/bin/activate
fi

pushd ${AIL_BIN}/helper/gen_cert
./gen_root.sh
wait
./gen_cert.sh
wait
popd

cp ${AIL_BIN}/helper/gen_cert/server.crt ${AIL_FLASK}/server.crt
cp ${AIL_BIN}/helper/gen_cert/server.key ${AIL_FLASK}/server.key

mkdir -p $AIL_HOME/PASTES

#Create the file all_module and update the graph in doc
$AIL_HOME/doc/generate_modules_data_flow_graph.sh

#### DB SETUP ####

# init update version
pushd ${AIL_HOME}
# shallow clone
git fetch --depth=500 --tags --prune
if [ ! -z "$TRAVIS" ]; then
    echo "Travis detected"
    git fetch --unshallow
fi
git describe --abbrev=0 --tags | tr -d '\n' > ${AIL_HOME}/update/current_version
echo "AIL current version:"
git describe --abbrev=0 --tags
popd

# LAUNCH ARDB
bash ${AIL_BIN}/LAUNCH.sh -lav &
wait
echo ""

# create default user
pushd ${AIL_FLASK}
python3 create_default_user.py
popd

bash ${AIL_BIN}/LAUNCH.sh -k &
wait
echo ""

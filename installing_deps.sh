#!/bin/bash

# halt on errors
set -e

## bash debug mode toggle below
#set -x

sudo apt-get update

sudo apt-get install python3-pip virtualenv python3-dev python3-tk libfreetype6-dev \
    screen g++ unzip libsnappy-dev cmake -qq

sudo apt-get install automake libtool make gcc pkg-config -qq

#Needed for downloading jemalloc
sudo apt-get install wget -qq

#Needed for bloom filters
sudo apt-get install libssl-dev libfreetype6-dev python3-numpy -qq

# pycld3
sudo apt-get install protobuf-compiler libprotobuf-dev -qq

# qrcode
sudo apt-get install python3-opencv -y
sudo apt-get install libzbar0 -y

# DNS deps
sudo apt-get install libadns1 libadns1-dev -qq

#Needed for redis-lvlDB
sudo apt-get install libev-dev libgmp-dev -qq # TODO NEED REVIEW

#Need for generate-data-flow graph
sudo apt-get install graphviz -qq

# ssdeep
sudo apt-get install libfuzzy-dev -qq
sudo apt-get install build-essential libffi-dev autoconf -qq

# sflock, gz requirement
sudo apt-get install p7zip-full -qq # TODO REMOVE ME

# SUBMODULES #
git submodule update --init

# REDIS #
test ! -d redis/ && git clone https://github.com/redis/redis.git
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
autoreconf -fiW all
./configure
make
sudo make install
popd

# ARDB #
#test ! -d ardb/ && git clone https://github.com/ail-project/ardb.git
#pushd ardb/
#make
#popd

DEFAULT_HOME=$(pwd)

#### KVROCKS ####
# If we are on debian, we can get the kvrocks deb package:
#   download the right version from https://github.com/RocksLabs/kvrocks-fpm/releases
#   then sudo dpkg -i kvrocks_2.11.1-1_amd64.deb   (change the version number to yours)
test ! -d kvrocks/ && git clone https://github.com/apache/incubator-kvrocks.git kvrocks
pushd kvrocks
./x.py build -j 4
popd

DEFAULT_KVROCKS_DATA=$DEFAULT_HOME/DATA_KVROCKS
mkdir -p $DEFAULT_KVROCKS_DATA

sed -i "s|dir /tmp/kvrocks|dir ${DEFAULT_KVROCKS_DATA}|1" $DEFAULT_HOME/configs/6383.conf
##-- KVROCKS --##



# Config File
if [ ! -f configs/core.cfg ]; then
    cp configs/core.cfg.sample configs/core.cfg
fi

# create AILENV + install python packages
./install_virtualenv.sh

# force virtualenv activation
if [ -z "$VIRTUAL_ENV" ]; then
    . ./AILENV/bin/activate
fi

pushd ${AIL_HOME}/tools/gen_cert
./gen_root.sh
wait
./gen_cert.sh
wait
popd

cp ${AIL_HOME}/tools/gen_cert/server.crt ${AIL_FLASK}/server.crt
cp ${AIL_HOME}/tools/gen_cert/server.key ${AIL_FLASK}/server.key

mkdir -p $AIL_HOME/PASTES

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

# LAUNCH Kvrocks
bash ${AIL_BIN}/LAUNCH.sh -lkv &
wait
echo ""

# create default user
pushd ${AIL_FLASK}
python3 create_default_user.py
popd

bash ${AIL_BIN}/LAUNCH.sh -k &
wait
echo ""

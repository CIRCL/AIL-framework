#!/bin/bash

set -e
set -x

sudo apt-get update

sudo apt-get install python-pip python-virtualenv python-dev libfreetype6-dev \
    screen g++ python-tk unzip libsnappy-dev

#Needed for bloom filters
sudo apt-get install libssl-dev libfreetype6-dev python-numpy

# DNS deps
sudo apt-get install libadns1 libadns1-dev

#Needed for redis-lvlDB
sudo apt-get install libev-dev libgmp-dev

#needed for mathplotlib
test ! -L /usr/include/ft2build.h && sudo ln -s freetype2/ft2build.h /usr/include/
sudo easy_install -U distribute

# REDIS #
test ! -d redis/ && git clone https://github.com/antirez/redis.git
pushd redis/
git checkout 2.8
make
popd

# REDIS LEVEL DB #
test ! -d redis-leveldb/ && git clone https://github.com/KDr2/redis-leveldb.git
pushd redis-leveldb/
git submodule init
git submodule update
make
popd

if [ ! -f bin/packages/config.cfg ]; then
    cp bin/packages/config.cfg.sample bin/packages/config.cfg
fi

virtualenv AILENV

echo export AIL_HOME=$(pwd) >> ./AILENV/bin/activate
echo export AIL_BIN=$(pwd)/bin/ >> ./AILENV/bin/activate
echo export AIL_FLASK=$(pwd)/var/www/ >> ./AILENV/bin/activate
echo export AIL_REDIS=$(pwd)/redis/src/ >> ./AILENV/bin/activate
echo export AIL_LEVELDB=$(pwd)/redis-leveldb/ >> ./AILENV/bin/activate

. ./AILENV/bin/activate

mkdir -p $AIL_HOME/{PASTES,Blooms,dumps}
mkdir -p $AIL_HOME/LEVEL_DB_DATA/{2014,2013}

pip install -r pip_packages_requirement.txt

# Download the necessary NLTK corpora
HOME=$(pwd) python -m textblob.download_corpora

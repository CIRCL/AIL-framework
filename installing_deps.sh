#!/bin/bash

set -e
set -x

sudo apt-get update

sudo apt-get install python-pip python-virtualenv python-dev libfreetype6-dev screen

virtualenv AILENV

echo export AIL_HOME=$(pwd) >> ./AILENV/bin/activate
echo export AIL_BIN=$(pwd)/bin/ >> ./AILENV/bin/activate
echo export AIL_FLASK=$(pwd)/var/www/ >> ./AILENV/bin/activate

sudo apt-get install g++ python-tk

#Needed for bloom filters
sudo apt-get install libssl-dev libfreetype6-dev python-numpy

# DNS deps
sudo apt-get install libadns1 libadns1-dev

#needed for mathplotlib
test ! -L /usr/include/ft2build.h && sudo ln -s freetype2/ft2build.h /usr/include/

. ./AILENV/bin/activate

pip install -r pip_packages_requirement.txt --upgrade

pip install -U textblob
python -m textblob.download_corpora

# REDIS #
test ! -d redis/ && git clone https://github.com/antirez/redis.git
pushd redis/
git checkout 2.8
git pull
make
popd

echo export AIL_REDIS=$(pwd)/src/ >> ./AILENV/bin/activate

# REDIS LEVEL DB #
test ! -d redis-leveldb/ && git clone https://github.com/KDr2/redis-leveldb.git
pushd redis-leveldb/
git submodule init
git submodule update
popd

mkdir -p $AIL_HOME/{PASTES,Blooms,dumps}

mkdir -p $AIL_HOME/LEVEL_DB_DATA/{2014,2013}


#!/bin/bash

set -e
set -x

sudo apt-get update

sudo apt-get install python-pip
sudo apt-get install python-virtualenv
sudo apt-get install python-dev
sudo apt-get install libfreetype6-dev
sudo apt-get install screen

virtualenv AILENV

echo export AIL_HOME=$(pwd) >> ./AILENV/bin/activate
echo export AIL_BIN=$(pwd)/bin/ >> ./AILENV/bin/activate
echo export AIL_FLASK=$(pwd)/var/www/ >> ./AILENV/bin/activate

sudo apt-get install g++
sudo apt-get install python-tk

#Needed for bloom filters
sudo apt-get install libssl-dev

sudo apt-get install libfreetype6-dev
sudo apt-get install python-numpy

#needed for mathplotlib
test ! -L /usr/include/ft2build.h && sudo ln -s freetype2/ft2build.h /usr/include/

. ./AILENV/bin/activate

pip install -r pip_packages_requirement.txt --upgrade

pip install -U textblob
python -m textblob.download_corpora

# REDIS #
test ! -d redis/ && git clone https://github.com/antirez/redis.git
cd redis/
git checkout 2.8
git pull
make

echo export AIL_REDIS = $(pwd)/src/ >> ./AILENV/bin/activate

# REDIS LEVEL DB #
cd $AIL_HOME
test ! -d redis-leveldb/ && git clone https://github.com/KDr2/redis-leveldb.git
cd redis-leveldb/
git submodule init
git submodule update

cd $AIL_HOME
mkdir -p PASTES
mkdir -p Blooms
mkdir -p dumps

mkdir -p LEVEL_DB_DATA
cd LEVEL_DB_DATA
mkdir -p 2014
mkdir -p 2013

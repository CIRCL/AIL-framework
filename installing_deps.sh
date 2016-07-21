#!/bin/bash

set -e
set -x

sudo apt-get update

sudo apt-get install python-pip python-virtualenv python-dev libfreetype6-dev \
    screen g++ python-tk unzip libsnappy-dev cmake

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
git checkout 3.2
make
popd

# Faup
test ! -d faup && git clone https://github.com/stricaud/faup.git
pushd faup/
test ! -d build && mkdir build
cd build
cmake .. && make
sudo make install
echo '/usr/local/lib' | sudo tee -a /etc/ld.so.conf.d/faup.conf
sudo ldconfig
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
mkdir -p $AIL_HOME/LEVEL_DB_DATA/2016

pip install -U pip
pip install -r pip_packages_requirement.txt

# Pyfaup
pushd faup/src/lib/bindings/python/
python setup.py install
popd


# Download the necessary NLTK corpora
HOME=$(pwd) python -m textblob.download_corpora

#!/bin/bash

# halt on errors
set -e

## bash debug mode togle below
#set -x

sudo apt-get update

sudo apt-get install python3-pip virtualenv python3-dev python3-tk libfreetype6-dev \
    screen g++ python-tk unzip libsnappy-dev cmake -qq

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
test ! -d ardb/ && git clone https://github.com/yinqiwen/ardb.git
pushd ardb/
make
popd

if [ ! -f bin/packages/config.cfg ]; then
    cp bin/packages/config.cfg.sample bin/packages/config.cfg
fi

if [ -z "$VIRTUAL_ENV" ]; then

    virtualenv -p python3 AILENV

    echo export AIL_HOME=$(pwd) >> ./AILENV/bin/activate
    echo export AIL_BIN=$(pwd)/bin/ >> ./AILENV/bin/activate
    echo export AIL_FLASK=$(pwd)/var/www/ >> ./AILENV/bin/activate
    echo export AIL_REDIS=$(pwd)/redis/src/ >> ./AILENV/bin/activate
    echo export AIL_ARDB=$(pwd)/ardb/src/ >> ./AILENV/bin/activate

    . ./AILENV/bin/activate

fi

pushd var/www/
./update_thirdparty.sh
popd

mkdir -p $AIL_HOME/PASTES

pip3 install -U pip
pip3 install 'git+https://github.com/D4-project/BGP-Ranking.git/@7e698f87366e6f99b4d0d11852737db28e3ddc62#egg=pybgpranking&subdirectory=client'
pip3 install -U -r requirements.txt

# Pyfaup
pushd faup/src/lib/bindings/python/
python3 setup.py install
popd

# Py tlsh
pushd tlsh/py_ext
python3 setup.py build
python3 setup.py install

# Download the necessary NLTK corpora and sentiment vader
HOME=$(pwd) python3 -m textblob.download_corpora
python3 -m nltk.downloader vader_lexicon
python3 -m nltk.downloader punkt

#Create the file all_module and update the graph in doc
$AIL_HOME/doc/generate_modules_data_flow_graph.sh

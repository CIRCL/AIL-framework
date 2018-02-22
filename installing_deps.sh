#!/bin/bash

set -e
set -x

sudo apt-get update

sudo apt-get install python-pip python-virtualenv python-dev libfreetype6-dev \
    screen g++ python-tk unzip libsnappy-dev cmake -y

#Needed for bloom filters
sudo apt-get install libssl-dev libfreetype6-dev python-numpy -y

#pyMISP
sudo apt-get -y install python3-pip

# DNS deps
sudo apt-get install libadns1 libadns1-dev -y

#Needed for redis-lvlDB
sudo apt-get install libev-dev libgmp-dev -y

#Need for generate-data-flow graph
sudo apt-get install graphviz -y

#needed for mathplotlib
sudo easy_install -U distribute
# ssdeep
sudo apt-get install libfuzzy-dev
sudo apt-get install build-essential libffi-dev automake autoconf libtool -y

# REDIS #
test ! -d redis/ && git clone https://github.com/antirez/redis.git
pushd redis/
git checkout 3.2
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
test ! -d tlsh && git clone git://github.com/trendmicro/tlsh.git
pushd tlsh/
./make.sh
pushd build/release/
sudo make install
sudo ldconfig
popd
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

pushd var/www/
./update_thirdparty.sh
popd

if [ -z "$VIRTUAL_ENV" ]; then

    virtualenv AILENV

    echo export AIL_HOME=$(pwd) >> ./AILENV/bin/activate
    echo export AIL_BIN=$(pwd)/bin/ >> ./AILENV/bin/activate
    echo export AIL_FLASK=$(pwd)/var/www/ >> ./AILENV/bin/activate
    echo export AIL_REDIS=$(pwd)/redis/src/ >> ./AILENV/bin/activate
    echo export AIL_LEVELDB=$(pwd)/redis-leveldb/ >> ./AILENV/bin/activate

    . ./AILENV/bin/activate

fi

year1=20`date +%y`
year2=20`date --date='-1 year' +%y`
mkdir -p $AIL_HOME/{PASTES,Blooms,dumps}
mkdir -p $AIL_HOME/LEVEL_DB_DATA/{$year1,$year2}

pip install -U pip
pip install -U -r pip_packages_requirement.txt
pip3 install -U -r pip3_packages_requirement.txt

# Pyfaup
pushd faup/src/lib/bindings/python/
python setup.py install
popd

# Py tlsh
pushd tlsh/py_ext
python setup.py build
python setup.py install
python3 setup.py build
python3 setup.py install

# Download the necessary NLTK corpora and sentiment vader
HOME=$(pwd) python -m textblob.download_corpora
python -m nltk.downloader vader_lexicon
python -m nltk.downloader punkt

#Create the file all_module and update the graph in doc
$AIL_HOME/doc/generate_modules_data_flow_graph.sh

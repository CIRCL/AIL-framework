#!/bin/bash

set -e
set -x

sudo apt-get update

sudo apt-get install python3-pip python-virtualenv python3-dev libfreetype6-dev \
    screen g++ python-tk unzip libsnappy-dev cmake -y

#optional tor install
sudo apt-get install tor -y

#Needed for bloom filters
sudo apt-get install libssl-dev libfreetype6-dev python-numpy -y

#pyMISP
#sudo apt-get -y install python3-pip

# DNS deps
sudo apt-get install libadns1 libadns1-dev -y

#Needed for redis-lvlDB
sudo apt-get install libev-dev libgmp-dev -y

#Need for generate-data-flow graph
sudo apt-get install graphviz -y

# install nosetests
sudo pip install nose -y

# ssdeep
sudo apt-get install libfuzzy-dev -y
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

year1=20`date +%y`
year2=20`date --date='-1 year' +%y`
mkdir -p $AIL_HOME/{PASTES,Blooms,dumps}

pip3 install -U pip
pip3 install -U -r pip3_packages_requirement.txt

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

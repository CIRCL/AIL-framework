#!/bin/bash


echo "Currently unmaintained, continue at your own risk of not having a working AIL at the end :( Will be merged into main install deps later on."
exit 1

set -e
set -x

sudo pacman -Syu

sudo pacman -S python2-pip screen gcc unzip freetype2 python2 git --needed
sudo yaourt -S snappy --needed
sudo pip2 install virtualenv

#Needed for bloom filters
sudo pacman -S openssl python2-numpy --needed

# DNS deps
sudo pacman -S adns --needed

#Needed for redis-lvlDB
sudo pacman -S libev gmp --needed

#needed for mathplotlib
test ! -L /usr/include/ft2build.h && sudo ln -s freetype2/ft2build.h /usr/include/
sudo easy_install-2.7 -U distribute

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



if [ ! -f bin/packages/config.cfg ]; then
    cp bin/packages/config.cfg.sample bin/packages/config.cfg
fi

pushd var/www/
./update_thirdparty.sh
popd

virtualenv AILENV

echo export AIL_HOME=$(pwd) >> ./AILENV/bin/activate
echo export AIL_BIN=$(pwd)/bin/ >> ./AILENV/bin/activate
echo export AIL_FLASK=$(pwd)/var/www/ >> ./AILENV/bin/activate
echo export AIL_REDIS=$(pwd)/redis/src/ >> ./AILENV/bin/activate
echo export AIL_LEVELDB=$(pwd)/redis-leveldb/ >> ./AILENV/bin/activate

. ./AILENV/bin/activate

mkdir -p $AIL_HOME/{PASTES,Blooms,dumps}
mkdir -p $AIL_HOME/LEVEL_DB_DATA/2017
mkdir -p $AIL_HOME/LEVEL_DB_DATA/3017

pip install -U pip
pip install -U -r pip_packages_requirement.txt

# Pyfaup
pushd faup/src/lib/bindings/python/
python setup.py install
popd

# Py tlsh
pushd tlsh/py_ext
python setup.py build
python setup.py install

# Download the necessary NLTK corpora and sentiment vader
HOME=$(pwd) python -m textblob.download_corpora
python -m nltk.downloader vader_lexicon
python -m nltk.downloader punkt

#Create the file all_module and update the graph in doc
$AIL_HOME/doc/generate_modules_data_flow_graph.sh

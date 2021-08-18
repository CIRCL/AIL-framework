#!/bin/bash
# halt on errors
set -e
sudo yum update
sudo yum -y -q install epel-release python3-pip virtualenv python3-devel python3-tkinter freetype-devel
sudo yum -y -q install screen
sudo yum -y -q install freetype-devel gcc gcc-c++ gcc-toolset-9-toolchain tk-devel unzip cmake
sudo yum -y -q --enablerepo=powertools install snappy-devel

#Needed for downloading jemalloc
sudo yum -y -q install wget

#optional tor install
sudo yum -y -q install tor

#Needed for bloom filters
sudo yum -y -q install openssl-devel python3-numpy

# DNS deps
#sudo wget https://forensics.cert.org/cert-forensics-tools-release-el8.rpm
#sudo rpm -Uvh cert-forensics-tools-release*rpm
#sudo yum -y -q --enablerepo=forensics install adns

#Needed for redis-lvlDB
sudo yum -y -q install libev-devel gmp-devel

#Need for generate-data-flow graph
sudo yum -y -q install graphviz

# install nosetests
sudo yum -y -q install python3-nose

# ssdeep
sudo yum -y -q install ssdeep-devel
sudo yum -y -q install gcc gcc-c++ make autoconf automake binutils bison flex gcc gcc-c++ gettext
sudo yum -y -q install libtool make patch pkgconfig redhat-rpm-config rpm-build rpm-sign
sudo yum -y -q install ctags elfutils indent patchutils libffi libffi-devel

# sflock, gz requirement
sudo yum -y -q install p7zip p7zip-plugins

#Install the Development Tools group of packages
sudo yum -y -q groupinstall "Development Tools"

#Static libraries for the GNU standard C++ library
sudo yum -y -q --enablerepo=powertools install libstdc++-static

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
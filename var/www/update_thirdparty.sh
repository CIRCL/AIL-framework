#!/bin/bash

# set -e

# submodules
git submodule update

rm -rf temp
mkdir temp

#### D3JS ####
#### TODO UPDATE ALL D3 JS to V7
wget https://d3js.org/d3.v7.min.js -O ./static/js/d3.v7.min.js

# OLD
D3_JS_VERSION='5.16.0'
wget https://github.com/d3/d3/releases/download/v${D3_JS_VERSION}/d3.zip -O  temp/d3_${D3_JS_VERSION}.zip
unzip -qq temp/d3_${D3_JS_VERSION}.zip -d temp/

mv temp/d3.min.js ./static/js/
#### ####

#### FONT_AWESOME ####
FONT_AWESOME_VERSION='6.6.0'
wget https://github.com/FortAwesome/Font-Awesome/archive/${FONT_AWESOME_VERSION}.zip -O temp/FONT_AWESOME_${FONT_AWESOME_VERSION}.zip
unzip temp/FONT_AWESOME_${FONT_AWESOME_VERSION}.zip -d temp/

rm -rf ./static/webfonts/
mv temp/Font-Awesome-${FONT_AWESOME_VERSION}/css/all.min.css ./static/css/font-awesome.min.css
mv temp/Font-Awesome-${FONT_AWESOME_VERSION}/webfonts ./static/webfonts

rm -rf ./static/fonts/ ./static/font-awesome/
mv temp/font-awesome/ ./static
#### ####

BOOTSTRAP_VERSION='4.2.1'

wget https://github.com/twbs/bootstrap/releases/download/v${BOOTSTRAP_VERSION}/bootstrap-${BOOTSTRAP_VERSION}-dist.zip -O temp/bootstrap${BOOTSTRAP_VERSION}.zip

# dateRangePicker
wget https://github.com/moment/moment/archive/2.24.0.zip -O temp/moment.zip
wget https://github.com/longbill/jquery-date-range-picker/archive/v0.20.0.zip -O temp/daterangepicker.zip

unzip -qq temp/bootstrap${BOOTSTRAP_VERSION}.zip -d temp/

unzip -qq temp/moment.zip -d temp/
unzip -qq temp/daterangepicker.zip -d temp/

mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/js/bootstrap.min.js ./static/js/bootstrap4.min.js
mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/js/bootstrap.min.js.map ./static/js/bootstrap.min.js.map
mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/css/bootstrap.min.css ./static/css/bootstrap4.min.css
mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/css/bootstrap.min.css.map ./static/css/bootstrap4.min.css.map


rm -rf ./static/css/plugins/
mv temp/jquery-date-range-picker-0.20.0/dist/daterangepicker.min.css ./static/css/

mv temp/moment-2.24.0/min/moment.min.js ./static/js/
mv temp/jquery-date-range-picker-0.20.0/dist/jquery.daterangepicker.min.js ./static/js/

JQVERSION="3.4.1"
wget http://code.jquery.com/jquery-${JQVERSION}.js -O ./static/js/jquery.js

#Ressources for dataTable
wget https://cdn.datatables.net/1.10.20/js/jquery.dataTables.min.js -O ./static/js/jquery.dataTables.min.js

wget https://cdn.datatables.net/1.10.20/css/dataTables.bootstrap4.min.css -O ./static/css/dataTables.bootstrap.min.css
wget https://cdn.datatables.net/1.10.20/js/dataTables.bootstrap4.min.js -O ./static/js/dataTables.bootstrap.min.js

#Ressource for graph
wget https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js -O ./static/js/echarts.min.js

#Ressources for bootstrap popover
POPPER_VERSION="1.16.1"
wget https://github.com/FezVrasta/popper.js/archive/v${POPPER_VERSION}.zip -O temp/popper.zip
unzip -qq temp/popper.zip -d temp/
mv temp/floating-ui-${POPPER_VERSION}/dist/umd/popper.min.js ./static/js/
mv temp/floating-ui-${POPPER_VERSION}/dist/umd/popper.min.js.map ./static/js/




# INSTALL YARA
YARA_VERSION="4.3.0"
wget https://github.com/VirusTotal/yara/archive/v${YARA_VERSION}.zip -O temp/yara.zip
unzip temp/yara.zip -d temp/
pushd temp/yara-${YARA_VERSION}
./bootstrap.sh
./configure
make
sudo make install
make check
popd


rm -rf temp

mkdir -p ./static/image
pushd static/image
wget -q https://www.circl.lu/assets/images/logos/AIL.png -O AIL.png
wget -q https://www.circl.lu/assets/images/logos/AIL-logo.png -O AIL-logo.png
popd

if ! [[ -n "$AIL_HOME" ]]
then
    #active virtualenv
    source ./../../AILENV/bin/activate
fi

#Update PyMISP
pip3 install pymisp --upgrade


#!/bin/bash

# set -e

# submodules
git submodule update

wget -q http://dygraphs.com/dygraph-combined.js -O ./static/js/dygraph-combined.js

BOOTSTRAP_VERSION='4.2.1'
FONT_AWESOME_VERSION='5.7.1'
D3_JS_VERSION='5.16.0'

rm -rf temp
mkdir temp

wget https://github.com/twbs/bootstrap/releases/download/v${BOOTSTRAP_VERSION}/bootstrap-${BOOTSTRAP_VERSION}-dist.zip -O temp/bootstrap${BOOTSTRAP_VERSION}.zip
wget https://github.com/FortAwesome/Font-Awesome/archive/v4.7.0.zip -O temp/FONT_AWESOME_4.7.0.zip
wget https://github.com/FortAwesome/Font-Awesome/archive/5.7.1.zip -O temp/FONT_AWESOME_${FONT_AWESOME_VERSION}.zip
wget https://github.com/d3/d3/releases/download/v${D3_JS_VERSION}/d3.zip -O  temp/d3_${D3_JS_VERSION}.zip

# dateRangePicker
wget https://github.com/moment/moment/archive/2.24.0.zip -O temp/moment.zip
wget https://github.com/longbill/jquery-date-range-picker/archive/v0.20.0.zip -O temp/daterangepicker.zip

unzip -qq temp/bootstrap${BOOTSTRAP_VERSION}.zip -d temp/
unzip -qq temp/FONT_AWESOME_4.7.0.zip -d temp/
unzip -qq temp/FONT_AWESOME_${FONT_AWESOME_VERSION}.zip -d temp/
unzip -qq temp/d3_${D3_JS_VERSION}.zip -d temp/

unzip -qq temp/moment.zip -d temp/
unzip -qq temp/daterangepicker.zip -d temp/

mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/js/bootstrap.min.js ./static/js/bootstrap4.min.js
mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/js/bootstrap.min.js.map ./static/js/bootstrap.min.js.map
mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/css/bootstrap.min.css ./static/css/bootstrap4.min.css
mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/css/bootstrap.min.css.map ./static/css/bootstrap4.min.css.map

mv temp/Font-Awesome-4.7.0 temp/font-awesome

rm -rf ./static/webfonts/
mv temp/Font-Awesome-${FONT_AWESOME_VERSION}/css/all.min.css ./static/css/font-awesome.min.css
mv temp/Font-Awesome-${FONT_AWESOME_VERSION}/webfonts ./static/webfonts

rm -rf ./static/js/plugins

rm -rf ./static/fonts/ ./static/font-awesome/
mv temp/font-awesome/ ./static/

rm -rf ./static/css/plugins/
mv temp/jquery-date-range-picker-0.20.0/dist/daterangepicker.min.css ./static/css/

mv temp/d3.min.js ./static/js/
mv temp/moment-2.24.0/min/moment.min.js ./static/js/
mv temp/jquery-date-range-picker-0.20.0/dist/jquery.daterangepicker.min.js ./static/js/

JQVERSION="3.4.1"
wget http://code.jquery.com/jquery-${JQVERSION}.js -O ./static/js/jquery.js

#Ressources for dataTable
wget https://cdn.datatables.net/1.10.20/js/jquery.dataTables.min.js -O ./static/js/jquery.dataTables.min.js
wget https://cdn.datatables.net/plug-ins/1.10.20/integration/bootstrap/3/dataTables.bootstrap.css -O ./static/css/dataTables.bootstrap.css
wget https://cdn.datatables.net/plug-ins/1.10.20/integration/bootstrap/3/dataTables.bootstrap.js -O ./static/js/dataTables.bootstrap.js

wget https://cdn.datatables.net/1.10.20/css/dataTables.bootstrap4.min.css -O ./static/css/dataTables.bootstrap.min.css
wget https://cdn.datatables.net/1.10.20/js/dataTables.bootstrap4.min.js -O ./static/js/dataTables.bootstrap.min.js

#Ressources for bootstrap popover
POPPER_VERSION="1.16.1"
wget https://github.com/FezVrasta/popper.js/archive/v${POPPER_VERSION}.zip -O temp/popper.zip
unzip -qq temp/popper.zip -d temp/
mv temp/floating-ui-${POPPER_VERSION}/dist/umd/popper.min.js ./static/js/
mv temp/floating-ui-${POPPER_VERSION}/dist/umd/popper.min.js.map ./static/js/

#Ressource for graph
# DASHBOARD   # TODO REFACTOR DASHBOARD GRAPHS
wget https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.js -O ./static/js/jquery.flot.js
wget https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.pie.js -O ./static/js/jquery.flot.pie.js
wget https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.time.js -O ./static/js/jquery.flot.time.js
wget https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.stack.js -O ./static/js/jquery.flot.stack.js

#Ressources for sparkline and canvasJS and slider
#wget http://omnipotent.net/jquery.sparkline/2.1.2/jquery.sparkline.min.js -O ./static/js/jquery.sparkline.min.js
#wget https://canvasjs.com/assets/script/canvasjs.min.js -O ./static/js/jquery.canvasjs.min.js

wget https://jqueryui.com/resources/download/jquery-ui-1.12.1.zip -O temp/jquery-ui.zip
unzip -qq temp/jquery-ui.zip -d temp/
mv temp/jquery-ui-1.12.1/jquery-ui.min.js ./static/js/jquery-ui.min.js
mv temp/jquery-ui-1.12.1/jquery-ui.min.css ./static/css/jquery-ui.min.css

# INSTALL YARA
YARA_VERSION="4.3.0"
wget https://github.com/VirusTotal/yara/archive/v${YARA_VERSION}.zip -O temp/yara.zip
unzip temp/yara.zip -d temp/
pushd temp/yara-${YARA_VERSION}
./bootstrap.sh
./configure
make -j
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


#!/bin/bash

set -e

wget http://dygraphs.com/dygraph-combined.js -O ./static/js/dygraph-combined.js

SBADMIN_VERSION='3.3.7'
FONT_AWESOME_VERSION='4.7.0'
D3_JS_VERSION='5.5.0'

rm -rf temp
mkdir temp

wget https://github.com/BlackrockDigital/startbootstrap-sb-admin/archive/v${SBADMIN_VERSION}.zip -O temp/${SBADMIN_VERSION}.zip
wget https://github.com/BlackrockDigital/startbootstrap-sb-admin-2/archive/v${SBADMIN_VERSION}.zip -O temp/${SBADMIN_VERSION}-2.zip
wget https://github.com/FortAwesome/Font-Awesome/archive/v${FONT_AWESOME_VERSION}.zip -O temp/FONT_AWESOME_${FONT_AWESOME_VERSION}.zip
wget https://github.com/d3/d3/releases/download/v${D3_JS_VERSION}/d3.zip -O  temp/d3_${D3_JS_VERSION}.zip

# dateRangePicker
wget https://github.com/moment/moment/archive/2.22.2.zip -O temp/moment_2.22.2.zip
wget https://github.com/longbill/jquery-date-range-picker/archive/v0.18.0.zip -O temp/daterangepicker_v0.18.0.zip


unzip temp/${SBADMIN_VERSION}.zip -d temp/
unzip temp/${SBADMIN_VERSION}-2.zip -d temp/
unzip temp/FONT_AWESOME_${FONT_AWESOME_VERSION}.zip -d temp/
unzip temp/d3_${D3_JS_VERSION}.zip -d temp/

unzip temp/moment_2.22.2.zip -d temp/
unzip temp/daterangepicker_v0.18.0.zip -d temp/

mv temp/startbootstrap-sb-admin-${SBADMIN_VERSION} temp/sb-admin
mv temp/startbootstrap-sb-admin-2-${SBADMIN_VERSION} temp/sb-admin-2
mv temp/Font-Awesome-${FONT_AWESOME_VERSION} temp/font-awesome

rm -rf ./static/js/plugins
mv temp/sb-admin/js/* ./static/js/

rm -rf ./static/fonts/ ./static/font-awesome/
mv temp/sb-admin/fonts/ ./static/
mv temp/font-awesome/ ./static/

rm -rf ./static/css/plugins/
mv temp/sb-admin/css/* ./static/css/
mv temp/sb-admin-2/dist/css/* ./static/css/
mv temp/jquery-date-range-picker-0.18.0/dist/daterangepicker.min.css ./static/css/

mv temp/d3.min.js ./static/js/
mv temp/moment-2.22.2/min/moment.min.js ./static/js/
mv temp/jquery-date-range-picker-0.18.0/dist/jquery.daterangepicker.min.js ./static/js/

rm -rf temp

JQVERSION="1.12.4"
wget http://code.jquery.com/jquery-${JQVERSION}.js -O ./static/js/jquery.js

#Ressources for dataTable
wget https://cdn.datatables.net/1.10.12/js/jquery.dataTables.min.js -O ./static/js/jquery.dataTables.min.js
wget https://cdn.datatables.net/plug-ins/1.10.7/integration/bootstrap/3/dataTables.bootstrap.css -O ./static/css/dataTables.bootstrap.css
wget https://cdn.datatables.net/plug-ins/1.10.7/integration/bootstrap/3/dataTables.bootstrap.js -O ./static/js/dataTables.bootstrap.js

#Ressource for graph
wget https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.js -O ./static/js/jquery.flot.js
wget https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.pie.js -O ./static/js/jquery.flot.pie.js
wget https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.time.js -O ./static/js/jquery.flot.time.js
wget https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.stack.js -O ./static/js/jquery.flot.stack.js

#Ressources for sparkline and canvasJS and slider
wget http://omnipotent.net/jquery.sparkline/2.1.2/jquery.sparkline.min.js -O ./static/js/jquery.sparkline.min.js
mkdir temp
wget http://canvasjs.com/fdm/chart/ -O temp/canvasjs.zip
unzip temp/canvasjs.zip -d temp/
mv temp/jquery.canvasjs.min.js ./static/js/jquery.canvasjs.min.js

wget https://jqueryui.com/resources/download/jquery-ui-1.12.0.zip -O temp/jquery-ui.zip
unzip temp/jquery-ui.zip -d temp/
mv temp/jquery-ui-1.12.0/jquery-ui.min.js ./static/js/jquery-ui.min.js
mv temp/jquery-ui-1.12.0/jquery-ui.min.css ./static/css/jquery-ui.min.css
rm -rf temp

mkdir -p ./static/image
pushd static/image
wget https://www.circl.lu/assets/images/logos/AIL.png -O AIL.png
popd

if ! [[ -n "$AIL_HOME" ]]
then
    #active virtualenv
    source ./../../AILENV/bin/activate
fi

#Update MISP Taxonomies and Galaxies
python3 -m pip install git+https://github.com/MISP/PyTaxonomies --upgrade
python3 -m pip install git+https://github.com/MISP/PyMISPGalaxies --upgrade

#Update PyMISP
python3 -m pip install git+https://github.com/MISP/PyMISP --upgrade

#Update the Hive
python3 -m pip install git+https://github.com/TheHive-Project/TheHive4py --upgrade

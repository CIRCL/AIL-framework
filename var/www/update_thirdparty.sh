#!/bin/bash

set -e

wget -q http://dygraphs.com/dygraph-combined.js -O ./static/js/dygraph-combined.js

SBADMIN_VERSION='3.3.7'
BOOTSTRAP_VERSION='4.2.1'
FONT_AWESOME_VERSION='5.7.1'
D3_JS_VERSION='5.5.0'

rm -rf temp
mkdir temp

wget -q https://github.com/twbs/bootstrap/releases/download/v${BOOTSTRAP_VERSION}/bootstrap-${BOOTSTRAP_VERSION}-dist.zip -O temp/bootstrap${BOOTSTRAP_VERSION}.zip
wget -q https://github.com/FezVrasta/popper.js/archive/v1.14.3.zip -O temp/popper.zip
wget -q https://github.com/BlackrockDigital/startbootstrap-sb-admin/archive/v${SBADMIN_VERSION}.zip -O temp/${SBADMIN_VERSION}.zip
wget -q https://github.com/BlackrockDigital/startbootstrap-sb-admin-2/archive/v${SBADMIN_VERSION}.zip -O temp/${SBADMIN_VERSION}-2.zip
wget -q https://github.com/FortAwesome/Font-Awesome/archive/v4.7.0.zip -O temp/FONT_AWESOME_4.7.0.zip
wget -q https://github.com/FortAwesome/Font-Awesome/archive/5.7.1.zip -O temp/FONT_AWESOME_${FONT_AWESOME_VERSION}.zip
wget -q https://github.com/d3/d3/releases/download/v${D3_JS_VERSION}/d3.zip -O  temp/d3_${D3_JS_VERSION}.zip

# dateRangePicker
wget -q https://github.com/moment/moment/archive/2.22.2.zip -O temp/moment_2.22.2.zip
wget -q https://github.com/longbill/jquery-date-range-picker/archive/v0.18.0.zip -O temp/daterangepicker_v0.18.0.zip

unzip -qq temp/bootstrap${BOOTSTRAP_VERSION}.zip -d temp/
unzip -qq temp/popper.zip -d temp/
unzip -qq temp/${SBADMIN_VERSION}.zip -d temp/
unzip -qq temp/${SBADMIN_VERSION}-2.zip -d temp/
unzip -qq temp/FONT_AWESOME_4.7.0.zip -d temp/
unzip -qq temp/FONT_AWESOME_${FONT_AWESOME_VERSION}.zip -d temp/
unzip -qq temp/d3_${D3_JS_VERSION}.zip -d temp/

unzip -qq temp/moment_2.22.2.zip -d temp/
unzip -qq temp/daterangepicker_v0.18.0.zip -d temp/

mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/js/bootstrap.min.js ./static/js/bootstrap4.min.js
mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/js/bootstrap.min.js.map ./static/js/bootstrap.min.js.map
mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/css/bootstrap.min.css ./static/css/bootstrap4.min.css
mv temp/bootstrap-${BOOTSTRAP_VERSION}-dist/css/bootstrap.min.css.map ./static/css/bootstrap4.min.css.map

mv temp/popper.js-1.14.3/dist/umd/popper.min.js ./static/js/
mv temp/popper.js-1.14.3/dist/umd/popper.min.js.map ./static/js/

mv temp/startbootstrap-sb-admin-${SBADMIN_VERSION} temp/sb-admin
mv temp/startbootstrap-sb-admin-2-${SBADMIN_VERSION} temp/sb-admin-2
mv temp/Font-Awesome-4.7.0 temp/font-awesome

rm -rf ./static/webfonts/
mv temp/Font-Awesome-${FONT_AWESOME_VERSION}/css/all.min.css ./static/css/font-awesome.min.css
mv temp/Font-Awesome-${FONT_AWESOME_VERSION}/webfonts ./static/webfonts

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
wget -q http://code.jquery.com/jquery-${JQVERSION}.js -O ./static/js/jquery.js

#Ressources for dataTable
wget -q https://cdn.datatables.net/1.10.12/js/jquery.dataTables.min.js -O ./static/js/jquery.dataTables.min.js
wget -q https://cdn.datatables.net/plug-ins/1.10.7/integration/bootstrap/3/dataTables.bootstrap.css -O ./static/css/dataTables.bootstrap.css
wget -q https://cdn.datatables.net/plug-ins/1.10.7/integration/bootstrap/3/dataTables.bootstrap.js -O ./static/js/dataTables.bootstrap.js

wget -q https://cdn.datatables.net/1.10.18/css/dataTables.bootstrap4.min.css -O ./static/css/dataTables.bootstrap.min.css
wget -q https://cdn.datatables.net/1.10.18/js/dataTables.bootstrap4.min.js -O ./static/js/dataTables.bootstrap.min.js

#Ressource for graph
wget -q https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.js -O ./static/js/jquery.flot.js
wget -q https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.pie.js -O ./static/js/jquery.flot.pie.js
wget -q https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.time.js -O ./static/js/jquery.flot.time.js
wget -q https://raw.githubusercontent.com/flot/flot/958e5fd43c6dff4bab3e1fd5cb6109df5c1e8003/jquery.flot.stack.js -O ./static/js/jquery.flot.stack.js

#Ressources for sparkline and canvasJS and slider
wget -q http://omnipotent.net/jquery.sparkline/2.1.2/jquery.sparkline.min.js -O ./static/js/jquery.sparkline.min.js
mkdir temp
wget -q http://canvasjs.com/fdm/chart/ -O temp/canvasjs.zip
unzip -qq temp/canvasjs.zip -d temp/
mv temp/jquery.canvasjs.min.js ./static/js/jquery.canvasjs.min.js

wget -q https://jqueryui.com/resources/download/jquery-ui-1.12.0.zip -O temp/jquery-ui.zip
unzip -qq temp/jquery-ui.zip -d temp/
mv temp/jquery-ui-1.12.0/jquery-ui.min.js ./static/js/jquery-ui.min.js
mv temp/jquery-ui-1.12.0/jquery-ui.min.css ./static/css/jquery-ui.min.css
rm -rf temp

mkdir -p ./static/image
pushd static/image
wget -q https://www.circl.lu/assets/images/logos/AIL.png -O AIL.png
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

#!/bin/bash

set -e

wget http://dygraphs.com/dygraph-combined.js -O ./static/js/dygraph-combined.js

SBADMIN_VERSION='3.3.7'

rm -rf temp
mkdir temp

wget https://github.com/BlackrockDigital/startbootstrap-sb-admin/archive/v${SBADMIN_VERSION}.zip -O temp/${SBADMIN_VERSION}.zip
wget https://github.com/BlackrockDigital/startbootstrap-sb-admin-2/archive/v${SBADMIN_VERSION}.zip -O temp/${SBADMIN_VERSION}-2.zip
unzip temp/${SBADMIN_VERSION}.zip -d temp/
unzip temp/${SBADMIN_VERSION}-2.zip -d temp/
mv temp/startbootstrap-sb-admin-${SBADMIN_VERSION} temp/sb-admin
mv temp/startbootstrap-sb-admin-2-${SBADMIN_VERSION} temp/sb-admin-2

rm -rf ./static/js/plugins
mv temp/sb-admin/js/* ./static/js/

rm -rf ./static/fonts/ ./static/font-awesome/
mv temp/sb-admin/fonts/ ./static/
mv temp/sb-admin/font-awesome/ ./static/

rm -rf ./static/css/plugins/
mv temp/sb-admin/css/* ./static/css/
mv temp/sb-admin-2/dist/css/* ./static/css/

rm -rf temp

JQVERSION="1.12.4"
wget http://code.jquery.com/jquery-${JQVERSION}.js -O ./static/js/jquery.js

#Ressources for dataTable
wget https://cdn.datatables.net/1.10.12/js/jquery.dataTables.min.js -O ./static/js/jquery.dataTables.min.js
wget https://cdn.datatables.net/plug-ins/1.10.7/integration/bootstrap/3/dataTables.bootstrap.css -O ./static/css/dataTables.bootstrap.css
wget https://cdn.datatables.net/plug-ins/1.10.7/integration/bootstrap/3/dataTables.bootstrap.js -O ./static/js/dataTables.bootstrap.js

#Ressource for graph
wget https://raw.githubusercontent.com/flot/flot/master/jquery.flot.js -O ./static/js/jquery.flot.js
wget https://raw.githubusercontent.com/flot/flot/master/jquery.flot.pie.js -O ./static/js/jquery.flot.pie.js
wget https://raw.githubusercontent.com/flot/flot/master/jquery.flot.time.js -O ./static/js/jquery.flot.time.js
wget https://raw.githubusercontent.com/flot/flot/master/jquery.flot.stack.js -O ./static/js/jquery.flot.stack.js

#Ressources for sparkline and canvasJS and slider
wget http://omnipotent.net/jquery.sparkline/2.1.2/jquery.sparkline.min.js -O ./static/js/jquery.sparkline.min.js
mkdir temp
wget http://canvasjs.com/fdm/chart/ -O temp/canvasjs.zip
unzip temp/canvasjs.zip -d temp/
mv temp/canvasjs-1.9.10-stable/jquery.canvasjs.min.js ./static/js/jquery.canvasjs.min.js

wget https://jqueryui.com/resources/download/jquery-ui-1.12.0.zip -O temp/jquery-ui.zip
unzip temp/jquery-ui.zip -d temp/
mv temp/jquery-ui-1.12.0/jquery-ui.min.js ./static/js/jquery-ui.min.js
mv temp/jquery-ui-1.12.0/jquery-ui.min.css ./static/css/jquery-ui.min.css
rm -rf temp

mkdir -p ./static/image
pushd static/image
wget https://www.circl.lu/assets/images/logos/AIL.png -O AIL.png
popd

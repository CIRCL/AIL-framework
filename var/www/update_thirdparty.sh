#!/bin/bash

set -e

wget http://dygraphs.com/dygraph-combined.js -O ./static/js/dygraph-combined.js

SBADMIN_VERSION='1.0.4'

rm -rf temp
mkdir temp

wget https://github.com/BlackrockDigital/startbootstrap-sb-admin/archive/v${SBADMIN_VERSION}.zip -O temp/${SBADMIN_VERSION}.zip
unzip temp/${SBADMIN_VERSION}.zip -d temp/
mv temp/startbootstrap-sb-admin-${SBADMIN_VERSION} temp/sb-admin-2

rm -rf ./static/js/plugins
mv temp/sb-admin-2/js/* ./static/js/

rm -rf ./static/fonts/ ./static/font-awesome/
mv temp/sb-admin-2/fonts/ ./static/
mv temp/sb-admin-2/font-awesome/ ./static/

rm -rf ./static/css/plugins/
mv temp/sb-admin-2/css/* ./static/css/

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

#Ressources for sparkline and canvasJS
wget http://omnipotent.net/jquery.sparkline/2.1.2/jquery.sparkline.min.js -O ./static/js/jquery.sparkline.min.js
mkdir temp
wget http://canvasjs.com/fdm/chart/ -O temp/canvasjs.zip
unzip temp/canvasjs.zip -d temp/
mv temp/jquery.canvasjs.min.js ./static/js/jquery.canvasjs.min.js
rm -rf temp

mkdir -p ./static/image
pushd static/image
wget https://www.circl.lu/assets/images/logos/AIL.png -O AIL.png
popd

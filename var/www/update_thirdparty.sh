#!/bin/bash

set -e

wget http://dygraphs.com/dygraph-combined.js -O ./static/js/dygraph-combined.js

SBADMIN_VERSION=2
filename="sb-admin-${SBADMIN_VERSION}"

rm -rf temp
mkdir temp

wget https://github.com/IronSummitMedia/startbootstrap-sb-admin-2/archive/v1.0.2.zip -O temp/${filename}".zip"
unzip temp/${filename}".zip" -d temp/
mv temp/startbootstrap-sb-admin-2-1.0.2 temp/sb-admin-2

JQVERSION="1.11.1"
wget http://code.jquery.com/jquery-${JQVERSION}.js -O ./static/js/jquery.js

#wget https://collabdev.googlecode.com/svn-history/r5/trunk/static/js/jquery.timers-1.0.0.js -O ./static/js/jquery.timers-1.0.0.js

#Here to fix an error about an hard dependency in a obscur script of bootstrap..
wget http://code.jquery.com/jquery-1.4.2.js -O ./static/js/jquery-1.4.2.js

wget http://www.goat1000.com/jquery.tagcanvas.js?2.5 -O ./static/js/jquery.tagcanvas.js

#Ressources for dataTable
wget https://cdn.datatables.net/1.10.12/js/jquery.dataTables.min.js -O ./static/js/jquery.dataTables.min.js
wget https://cdn.datatables.net/plug-ins/1.10.7/integration/bootstrap/3/dataTables.bootstrap.css -O ./static/css/dataTables.bootstrap.css
wget https://cdn.datatables.net/plug-ins/1.10.7/integration/bootstrap/3/dataTables.bootstrap.js -O ./static/js/dataTables.bootstrap.js

#Ressource for graph
wget https://raw.githubusercontent.com/flot/flot/master/jquery.flot.js -O ./static/js/jquery.flot.js
wget https://raw.githubusercontent.com/flot/flot/master/jquery.flot.pie.js -O ./static/js/jquery.flot.pie.js

rm -rf ./static/js/plugins
mv temp/${filename}/js/* ./static/js/

rm -rf ./static/fonts/ ./static/font-awesome-4.1.0/

mv temp/${filename}/fonts/ ./static/
mv temp/${filename}/font-awesome/ ./static/

rm -rf ./static/css/plugins/
mv temp/${filename}/css/* ./static/css/

rm -rf temp/
mkdir -p ./static/image
cd static/image
wget https://www.circl.lu/assets/images/logos/AIL.png -O AIL.png

cd ../..


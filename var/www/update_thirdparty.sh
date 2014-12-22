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

wget https://collabdev.googlecode.com/svn-history/r5/trunk/static/js/jquery.timers-1.0.0.js -O ./static/js/jquery.timers-1.0.0.js

#Here to fix an error about an hard dependency in a obscur script of bootstrap..
wget http://code.jquery.com/jquery-1.4.2.js -O ./static/js/jquery-1.4.2.js

wget http://www.goat1000.com/jquery.tagcanvas.js?2.5 -O ./static/js/jquery.tagcanvas.js

rm -rf ./static/js/plugins
mv temp/${filename}/js/* ./static/js/

rm -rf ./static/fonts/ ./static/font-awesome-4.1.0/

mv temp/${filename}/fonts/ ./static/
mv temp/${filename}/font-awesome/ ./static/

rm -rf ./static/css/plugins/
mv temp/${filename}/css/* ./static/css/

rm -rf temp/

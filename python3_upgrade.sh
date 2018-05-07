#!/bin/bash

sudo rm -rf AILENV
mkdir old
sudo mv indexdir old/old_indexdir_python2
sudo mv LEVEL_DB_DATA old/old_LEVEL_DB_DATA

./installing_deps.sh

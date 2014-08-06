#!/bin/bash

set -e
set -x

sudo apt-get update

sudo apt-get install python-pip
sudo apt-get install python-virtualenv
sudo apt-get install python-dev
sudo apt-get install libfreetype6-dev


virtualenv AILENV

. ./AILENV/bin/activate

pip install -r requirements.txt --upgrade

python -m textblob.download_corpora
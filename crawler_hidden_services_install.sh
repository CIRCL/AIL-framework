#!/bin/bash

# install docker
sudo apt install docker.io

# pull splah docker
sudo docker pull scrapinghub/splash

. ./AILENV/bin/activate
pip3 install -U -r pip3_packages_requirement.txt

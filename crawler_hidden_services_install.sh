#!/bin/bash

read -p "Do you want to install docker? (use local splash server) [y/n] " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    # install docker
    sudo apt install docker.io
fi

# pull splah docker
sudo docker pull scrapinghub/splash

. ./AILENV/bin/activate
pip3 install -U -r pip3_packages_requirement.txt

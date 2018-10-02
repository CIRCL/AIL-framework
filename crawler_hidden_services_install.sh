#!/bin/bash

install_docker() {
    # install docker
    sudo apt install docker.io;

    # pull splah docker
    sudo docker pull scrapinghub/splash;
}

install_python_requirement() {
    . ./AILENV/bin/activate;
    pip3 install -U -r crawler_requirements.txt;
}

install_all() {
    read -p "Do you want to install docker? (use local splash server) [y/n] " -n 1 -r
    echo    # (optional) move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        install_docker;
    fi
    install_python_requirement;
}

usage() {
  echo "Usage: crawler_hidden_services_install.sh [-y | -n]" 1>&2;
            echo "          -y: install docker"
            echo "          -n: don't install docker"
            echo ""
            echo "example:"
            echo "crawler_hidden_services_install.sh -y"
            exit 1;
}

if [[ $1 == "" ]]; then
    install_all;
    exit;
else
  key="$1"
  case $key in
      "")
      install_all;
      ;;
      -y|--yes)
      install_docker;
      install_python_requirement;
      ;;
      -n|--no)
      install_python_requirement;
      ;;
      *)    # unknown option
      usage;
      ;;
  esac
fi

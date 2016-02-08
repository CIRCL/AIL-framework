[![Build Status](https://travis-ci.org/CIRCL/AIL-framework.svg?branch=master)](https://travis-ci.org/CIRCL/AIL-framework)

AIL
===

AIL framework - Framework for Analysis of Information Leaks

AIL is a modular framework to analyse potential information leaks from unstructured data sources like pastes from Pastebin or similar services. AIL framework is flexible and can be extended to support other functionalities to mine sensitive information.

![Dashboard](./doc/screenshots/DashboardAIL.png?raw=true "AIL framework dashboard")
![Trending](./doc/screenshots/WordtrendingAIL.png?raw=true "AIL framework wordtrending")

AIL framework screencast: https://www.youtube.com/watch?v=9idfHCIMzBY

Requirements & Installation
---------------------------

Auto installation
-----------------
Type these command lines for a fully automated installation and start AIL framework
```
git clone https://github.com/CIRCL/AIL-framework.git
cd AIL-framework
./installing_deps.sh
cd var/www/
./update_thirdparty.sh
cd ~/AIL-framework/
. ./AILENV/bin/activate
cd bin/
./LAUNCH.sh
```

Manual installation
-------------------
As AIL is based on python, obviously an installation of python is a requirement:
``sudo apt-get install python2.7``

In addition pip, virtualenv and screen are needed:
```
sudo apt-get install python-pip
sudo pip install virtualenv
sudo apt-get install screen
sudo apt-get install unzip
```

You need to create a variable AILENV that will be the installation path:

``export AILENV="/home/user/AIL-framework"``

Usually the installation path is where the project is cloned.

Then create a Python virtual environment:

```
cd $AILENV
virtualenv AILENV
```

And install these few more packets:
```
sudo apt-get install g++
sudo apt-get install python-dev
sudo apt-get install python-tk
sudo apt-get install screen
sudo apt-get install libssl-dev
sudo apt-get install libfreetype6-dev
sudo apt-get install python-numpy
sudo apt-get install libadns1
sudo apt-get install libadns1-dev
sudo apt-get install libev-dev (redis-levelDB dependency)
sudo apt-get install libgmp-dev (redis-levelDB dependency)
```

Then these modules need to be install with pip inside the virtual environment:
(Activating virtualenv)
```
. ./AILENV/bin/activate
```

You'll need to clone langid:
[https://github.com/saffsd/langid.py]
And install it:
```
python setup.py install
```

These are all the packages you can install with pip:

```
pip install redis
pip install logbook
pip install pubsublogger
pip install networkx
pip install crcmod
pip install mmh3
pip install dnspython
pip install pyzmq
pip install texttable
pip install -U textblob
python -m textblob.download_corpora
pip install python-magic
pip install numpy
pip install flask
pip install nltk
pip install whoosh
pip install matplotlib ----- (sudo ln -s freetype2/ft2build.h in /usr/include/)
pip install pybloomfiltermmap ----- (you may need to sudo apt-get install libssl-dev)
pip install ipaddress
pip install http://adns-python.googlecode.com/files/adns-python-1.2.1.tar.gz
pip install https://github.com/trolldbois/python-cymru-services/archive/master.zip
```

Installing Redis & Level DB
---------------------------

Assuming that you install everything under /opt/ with adequate permissions:

```
wget http://download.redis.io/releases/redis-2.8.12.tar.gz
tar -xvf redis-2.8.12.tar.gz -C /opt/
```
And follow the README after extraction.

When redis is properly installed you can edit your own config files for
the different required databases or just take the config from the project
located under ``/config/``

```
git clone https://github.com/KDr2/redis-leveldb.git
```
Follow the redis-leveldb README.

Then create these directories

```
cd $AILENV
	mkdir PASTES
	mkdir Blooms
	mkdir dumps

mkdir LEVEL_DB_DATA
cd LEVEL_DB_DATA/
	mkdir 2014
	mkdir 2013
```

Starting AIL
------------

If you installed all the requirements described above, you should be able to start AIL framework:

```
cd $AILENV
cd bin
./LAUNCH.sh
```

To start with the web interface, you need to fetch the required Javascript/CSS files:

```
cd $AILENV
cd var/www/
bash update_thirdparty.sh
```

and then you can start the web interface:

```
cd $AILENV
cd var/www/
Flask_server.py
```

Eventually you can browse the status of the AIL framework at the following URL:

        ``http://localhost:7000/``

How to create a new module
--------------------------

If you want to add a new processing or analysis module in AIL, it's simple.

1. Add your module name in [./bin/packages/modules.cfg](./bin/packages/modules.cfg) and subscribe to the Redis_Global at minimum.

2. Use [./bin/template.py](./bin/template.py) as a sample module and create a new file in bin/ with the module name used in the modules.cfg configuration.



Redis and LevelDB overview
--------------------------

* Redis on TCP port 6379 - DB 1 - Paste meta-data
*                          DB 0 - Cache hostname/dns
* Redis on TCP port 6380 - Redis Pub-Sub only
* Redis on TCP port 6381 - DB 0 - Queue and Paste content LRU cache
* LevelDB on TCP port <year> - Lines duplicate

LICENSE
-------

```
    Copyright (C) 2014 Jules Debra
    Copyright (C) 2014-2016 CIRCL - Computer Incident Response Center Luxembourg (c/o smile, security made in Lëtzebuerg, Groupement d'Intérêt Economique)
    Copyright (c) 2014-2016 Raphaël Vinot
    Copyright (c) 2014-2016 Alexandre Dulaunoy

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
```


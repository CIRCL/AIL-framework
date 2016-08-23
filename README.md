[![Build Status](https://travis-ci.org/CIRCL/AIL-framework.svg?branch=master)](https://travis-ci.org/CIRCL/AIL-framework)

AIL
===

![Logo](./doc/logo/logo-small.png?raw=true "AIL logo")

AIL framework - Framework for Analysis of Information Leaks

AIL is a modular framework to analyse potential information leaks from unstructured data sources like pastes from Pastebin or similar services. AIL framework is flexible and can be extended to support other functionalities to mine sensitive information.

![Dashboard](./doc/screenshots/dashboard.png?raw=true "AIL framework dashboard")

Trending
--------

![Trending-Web](./doc/screenshots/trending-web.png?raw=true "AIL framework webtrending")
![Trending-Modules](./doc/screenshots/trending-module.png?raw=true "AIL framework modulestrending")

Browsing
--------

![Browse-Pastes](./doc/screenshots/browse-important.png?raw=true "AIL framework browseImportantPastes")

Sentiment analysis
------------------

![Sentiment](./doc/screenshots/sentiment.png?raw=true "AIL framework sentimentanalysis")

Terms manager and occurence
---------------------------

![Term-Manager](./doc/screenshots/terms-manager.png?raw=true "AIL framework termManager")
![Term-Top](./doc/screenshots/terms-top.png?raw=true "AIL framework termTop")
![Term-Plot](./doc/screenshots/terms-plot.png?raw=true "AIL framework termPlot")


AIL framework screencast: https://www.youtube.com/watch?v=9idfHCIMzBY

Features
--------

* Modular architecture to handle streams of unstructured or structured information
* Default support for external ZMQ feeds, such as provided by CIRCL or other providers
* Each module can process and reprocess the information already processed by AIL
* Detecting and extracting URLs including their geographical location (e.g. IP address location)
* Extracting and validating potential leak of credit cards numbers
* Extracting and validating email addresses leaked including DNS MX validation
* Module for extracting Tor .onion addresses (to be further processed for analysis)
* Extracting and validating potential hostnames (e.g. to feed Passive DNS systems)
* A full-text indexer module to index unstructured information
* Modules and web statistics 
* Global sentiment analysis for each providers based on nltk vader module
* Terms tracking and occurence
* Many more modules for extracting phone numbers, credentials and others

Installation
------------

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
The default [installing_deps.sh](./installing_deps.sh) is for Debian and Ubuntu based distributions. For Arch
linux based distributions, you can replace it with [installing_deps_archlinux.sh](./installing_deps_archlinux.sh).

There is also a [Travis file](.travis.yml) used for automating the installation that can be used to build and install AIL on other systems.

Concerning the sentiment module, nltk.sentiment.vader must be installed manually.

In your AIL virtualenv, type
```
python
import nltk
nltk.download()
```
and then install the sentiment.vader module


Starting AIL web interface
--------------------------

To start the web interface, you first need to fetch the required Javascript/CSS files:

```
cd $AILENV
cd var/www/
bash update_thirdparty.sh
```

and then you can start the web interface python script:

```
cd $AILENV
cd var/www/
Flask_server.py
```

Eventually you can browse the status of the AIL framework website at the following URL:

        ``http://localhost:7000/``

How to create a new module
--------------------------

If you want to add a new processing or analysis module in AIL, follow these simple steps:

1. Add your module name in [./bin/packages/modules.cfg](./bin/packages/modules.cfg) and subscribe to the Redis_Global at minimum.

2. Use [./bin/template.py](./bin/template.py) as a sample module and create a new file in bin/ with the module name used in the modules.cfg configuration.

How to contribute a module
--------------------------

Feel free to fork the code, play with it, make some patches or add additional analysis modules.

To contribute your module, feel free to pull your contribution.

Redis and LevelDB overview
--------------------------

* Redis on TCP port 6379 - DB 1 - Paste meta-data
*                          DB 0 - Cache hostname/dns
* Redis on TCP port 6380 - Redis Pub-Sub only
* Redis on TCP port 6381 - DB 0 - Queue and Paste content LRU cache
* Redis on TCP port 6382 - DB 1-4 - Trending, terms and sentiments
* LevelDB on TCP port <year> - Lines duplicate

LICENSE
-------

```
    Copyright (C) 2014 Jules Debra
    Copyright (C) 2014-2016 CIRCL - Computer Incident Response Center Luxembourg (c/o smile, security made in Lëtzebuerg, Groupement d'Intérêt Economique)
    Copyright (c) 2014-2016 Raphaël Vinot
    Copyright (c) 2014-2016 Alexandre Dulaunoy
    Copyright (c) 2016 Sami Mokaddem

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


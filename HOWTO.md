
# Feeding, adding new features and contributing

## [Documentation AIL Importers](./doc/README.md#ail-importers)

[Documentation AIL Importers](./doc/README.md#ail-importers)

## How to feed the AIL framework

AIL is an analysis tool, not a collector!
However, if you want to collect some pastes and feed them to AIL, the procedure is described below. Nevertheless, moderate your queries!

1. [AIL Importers](./doc/README.md#ail-importers)

2. ZMQ: Be a collaborator of CIRCL and ask to access our feed. It will be sent to the static IP you are using for AIL.

## How to create a new module

To add a new processing or analysis module to AIL, follow these steps:

1. Add your module name in [./configs/modules.cfg](./configs/modules.cfg) and subscribe to at least one module at minimum (Usually, `Item`).

2. Use [./bin/modules/modules/TemplateModule.py](./bin/modules/modules/TemplateModule.py) as a sample module and create a new file in bin/modules with the module name used in the `modules.cfg` configuration.


## How to contribute a module

Feel free to fork the code, play with it, make some patches or add additional analysis modules.

To contribute your module, feel free to pull your contribution.


## Additional information

### Crawler

In AIL, you can crawl websites and Tor hidden services. Don't forget to review the proxy configuration of your Tor client and especially if you enabled the SOCKS5 proxy

### Installation

[Install Lacus](https://github.com/ail-project/lacus)

### Configuration

1. Lacus URL:  
In the web interface, go to `Crawlers` > `Settings` and click on the Edit button

![Splash Manager Config](./doc/screenshots/lacus_config.png?raw=true "AIL Lacus Config")

![Splash Manager Config](./doc/screenshots/lacus_config_edit.png?raw=true "AIL Lacus Config")

2. Launch AIL Crawlers:   
Choose the number of crawlers you want to launch

![Splash Manager Nb Crawlers Config](./doc/screenshots/crawler_nb_captures.png?raw=true "AIL Lacus Nb Crawlers Config")

![Splash Manager Nb Crawlers Config](./doc/screenshots/crawler_nb_captures_edit.png?raw=true "AIL Lacus Nb Crawlers Config")


### Kvrocks Migration
---------------------
**Important Note:
We are currently working on a [migration script](https://github.com/ail-project/ail-framework/blob/master/bin/DB_KVROCKS_MIGRATION.py) to facilitate the migration to Kvrocks. 
Once this script is ready, AIL version 5.0 will be released.**

Please note that the current version of this migration script only supports migrating the database on the same server.
(If you plan to migrate to another server, we will provide additional instructions in this section once the migration script is completed)

To migrate your database to Kvrocks:
1. Launch ARDB and Kvrocks
2. Pull from remote
	```shell
	git checkout master
	git pull
 	```
3. Launch the migration script:
	```shell
	git checkout master
	git pull
	cd bin/
	./DB_KVROCKS_MIGRATION.py
	```

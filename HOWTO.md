
# Feeding, adding new features and contributing

## How to feed the AIL framework

Currently, there are three different ways to feed data into AIL:

1. Be a collaborator of CIRCL and ask to access our feed. It will be sent to the static IP you are using for AIL.

2. You can setup [pystemon](https://github.com/cvandeplas/pystemon) and use the custom feeder provided by AIL (see below).

3. You can feed your own data using the [./tool/file_dir_importer.py](./tool/file_dir_importer.py) script.

### Feeding AIL with pystemon

AIL is an analysis tool, not a collector!
However, if you want to collect some pastes and feed them to AIL, the procedure is described below. Nevertheless, moderate your queries!

Feed data to AIL:

1. Clone the [pystemon's git repository](https://github.com/cvandeplas/pystemon):
	```
	git clone https://github.com/cvandeplas/pystemon.git
 	```

2. Edit configuration file for pystemon ```pystemon/pystemon.yaml```: 
	- Configure the storage section according to your needs:
		```
		storage:  
			archive:  
				storage-classname:  FileStorage  
				save: yes  
				save-all: yes  
				dir: "alerts"  
				dir-all: "archive"  
				compress: yes
			
			redis:  
				storage-classname:  RedisStorage  
				save: yes  
				save-all: yes  
				server: "localhost"  
				port: 6379  
				database: 10  
				lookup: no
		```
	- Adjust the configuration for paste-sites based on your requirements (remember to throttle download and update times).
   
3. Install python dependencies inside the virtual environment:
	```shell
	cd ail-framework/
	. ./AILENV/bin/activate
	cd pystemon/
	pip install -U -r requirements.txt
	``` 
4. Edit the configuration file ```ail-framework/configs/core.cfg```:
	- Modify the "pystemonpath" path accordingly.

5. Launch ail-framework, pystemon and PystemonImporter.py (all within the virtual environment):
	 - Option 1 (recommended): 
		``` 
		 ./ail-framework/bin/LAUNCH.py -l #starts ail-framework
		 ./ail-framework/bin/LAUNCH.py -f #starts pystemon and the PystemonImporter.py
		```
     - Option 2 (may require two terminal windows): 
        ``` 
        ./ail-framework/bin/LAUNCH.py -l #starts ail-framework
        ./pystemon/pystemon.py
        ./ail-framework/bin/importer/PystemonImporter.py
        ```

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

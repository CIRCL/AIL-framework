
Feeding, adding new features and contributing
=============================================

How to feed the AIL framework
-----------------------------

For the moment, there are three different ways to feed AIL with data:

1. Be a collaborator of CIRCL and ask to access our feed. It will be sent to the static IP you are using for AIL.

2. You can setup [pystemon](https://github.com/cvandeplas/pystemon) and use the custom feeder provided by AIL (see below).

3. You can feed your own data using the [./bin/import_dir.py](./bin/import_dir.py) script.

### Feeding AIL with pystemon

AIL is an analysis tool, not a collector!
However, if you want to collect some pastes and feed them to AIL, the procedure is described below. Nevertheless, moderate your queries!

Feed data to AIL:

1. Clone the [pystemon's git repository](https://github.com/cvandeplas/pystemon):
``` git clone https://github.com/cvandeplas/pystemon.git ```

2. Edit configuration file for pystemon ```pystemon/pystemon.yaml```: 
	* Configuration of storage section (adapt to your needs):
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
	* Change configuration for paste-sites according to your needs (don't forget to throttle download time and/or update time).
3. Install python dependencies inside the virtual environment:
	``` 
	cd ail-framework/
	. ./AILENV/bin/activate
	cd pystemon/ #cd to pystemon folder
	pip3 install -U -r requirements.txt
	``` 
4. Edit configuration file ```ail-framework/configs/core.cfg```:
	* Modify the "pystemonpath" path accordingly

5. Launch ail-framework, pystemon and pystemon-feeder.py (still inside virtual environment):
	 * Option 1 (recommended): 
		 ``` 
		 ./ail-framework/bin/LAUNCH.py -l #starts ail-framework
		 ./ail-framework/bin/LAUNCH.py -f #starts pystemon and the pystemon-feeder.py
		```
	* Option 2 (you may need two terminal windows): 
		 ``` 
		 ./ail-framework/bin/LAUNCH.py -l #starts ail-framework
		 ./pystemon/pystemon.py
		 ./ail-framework/bin/feeder/pystemon-feeder.py
		 ```

How to create a new module
--------------------------

If you want to add a new processing or analysis module in AIL, follow these simple steps:

1. Add your module name in [./bin/packages/modules.cfg](./bin/packages/modules.cfg) and subscribe to at least one module at minimum (Usually, Redis_Global).

2. Use [./bin/template.py](./bin/template.py) as a sample module and create a new file in bin/ with the module name used in the modules.cfg configuration.


How to create a new webpage
---------------------------

If you want to add a new webpage for a module in AIL, follow these simple steps:

1. Launch [./var/www/create_new_web_module.py](./var/www/create_new_web_module.py) and enter the name to use for your webpage (Usually, your newly created python module).

2. A template and flask skeleton has been created for your new webpage in [./var/www/modules/](./var/www/modules/)

3. Edit the created html files under the template folder as well as the Flask_* python script so that they fit your needs.

4. You can change the order of your module in the top navigation header in the file [./var/www/templates/header_base.html](./var/www/templates/header_base.html)

5. You can ignore module, and so, not display them in the top navigation header by adding the module name in the file [./var/www/templates/ignored_modules.txt](./var/www/templates/ignored_modules.txt)

How to contribute a module
--------------------------

Feel free to fork the code, play with it, make some patches or add additional analysis modules.

To contribute your module, feel free to pull your contribution.


Additional information
======================

Manage modules: ModulesInformationV2.py
---------------------------------------

You can do a lots of things easily with the [./bin/ModulesInformationV2](./bin/ModulesInformationV2) script:

- Monitor the health of other modules
- Monitor the ressources comsumption of other modules
- Start one or more modules
- Kill running modules
- Restart automatically stuck modules
- Show the paste currently processed by a module

### Navigation

You can navigate into the interface by using arrow keys. In order to perform an action on a selected module, you can either press <ENTER> or <SPACE> to show the dialog box.

To change list, you can press the <TAB> key.

Also, you can quickly stop or start modules by clicking on the ``<K>`` or ``<S>`` symbol respectively. These are located in the _Action_ column.

Finally, you can quit this program by pressing either ``<q>`` or ``<C-c>``.



Crawler
---------------------

In AIL, you can crawl websites and Tor hidden services. Don't forget to review the proxy configuration of your Tor client and especially if you enabled the SOCKS5 proxy

[//]: # (and binding on the appropriate IP address reachable via the dockers where Splash runs.)

### Installation


[Install Lacus](https://github.com/ail-project/lacus)

### Configuration

1. Lacus URL:  
In the webinterface, go to ``Crawlers>Settings`` and click on the Edit button

![Splash Manager Config](./doc/screenshots/lacus_config.png?raw=true "AIL Lacus Config")

![Splash Manager Config](./doc/screenshots/lacus_config_edit.png?raw=true "AIL Lacus Config")

2. Launch AIL Crawlers:   
Choose the number of crawlers you want to launch

![Splash Manager Nb Crawlers Config](./doc/screenshots/crawler_nb_captures.png?raw=true "AIL Lacus Nb Crawlers Config")
![Splash Manager Nb Crawlers Config](./doc/screenshots/crawler_nb_captures_edit.png?raw=true "AIL Lacus Nb Crawlers Config")



#### Old updates

##### Python 3 Upgrade

To upgrade from an existing AIL installation, you have to launch [python3_upgrade.sh](./python3_upgrade.sh), this script will delete and create a new virtual environment. The script **will upgrade the packages but won't keep your previous data** (neverthless the data is copied into a directory called `old`). If you install from scratch, you don't require to launch the [python3_upgrade.sh](./python3_upgrade.sh).

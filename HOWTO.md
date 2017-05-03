How to
======

How to feed the AIL framework
-----------------------------

For the moment, there are three different ways to feed AIL with data:

1. Be a collaborator of CIRCL and ask to access our feed. It will be sent to the static IP your are using for AIL.

2. You can setup [pystemon](https://github.com/CIRCL/pystemon) and use the custom feeder provided by AIL (see below).

3. You can feed your own data using the [./bin/import_dir.py](./bin/import_dir.py) script.

Feeding AIL with pystemon
-------------------------

AIL is an analysis tool, not a collector!
However, if you want to collect some pastes and feed them to AIL, the procedure is described below.

Nevertheless, moderate your queries!

Feed data to AIL:

1. Clone the [pystemon's git repository](https://github.com/CIRCL/pystemon)

2. Install its python dependencies inside your virtual environment

3. Launch pystemon ``` ./pystemon ```

4. Edit your configuration file ```bin/packages/config.cfg``` and modify the pystemonpath path accordingly

5. Launch pystemon-feeder ``` ./pystemon-feeder.py ```


How to create a new module
--------------------------

If you want to add a new processing or analysis module in AIL, follow these simple steps:

1. Add your module name in [./bin/packages/modules.cfg](./bin/packages/modules.cfg) and subscribe to at least one module at minimum (Usually, Redis_Global).

2. Use [./bin/template.py](./bin/template.py) as a sample module and create a new file in bin/ with the module name used in the modules.cfg configuration.


How to create a new webpage
---------------------------

If you want to add a new webpage for a module in AIL, follow these simple steps:

1. Launch [./var/www/create_new_web_module.py](./var/www/create_new_web_module.py) and enter the name to use for your webpage (Usually, your python module).

2. A template and flask skeleton has been created for your new webpage in [./var/www/modules/](./var/www/modules/)

3. Edit the created html files under the template folder as well as the Flask_* python script.

How to contribute a module
--------------------------

Feel free to fork the code, play with it, make some patches or add additional analysis modules.

To contribute your module, feel free to pull your contribution.


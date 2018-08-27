Feeding, adding new features and contributing
=============================================

How to feed the AIL framework
-----------------------------

For the moment, there are three different ways to feed AIL with data:

1. Be a collaborator of CIRCL and ask to access our feed. It will be sent to the static IP you are using for AIL.

2. You can setup [pystemon](https://github.com/CIRCL/pystemon) and use the custom feeder provided by AIL (see below).

3. You can feed your own data using the [./bin/import_dir.py](./bin/import_dir.py) script.

### Feeding AIL with pystemon

AIL is an analysis tool, not a collector!
However, if you want to collect some pastes and feed them to AIL, the procedure is described below. Nevertheless, moderate your queries!

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

Also, you can quickly stop or start modules by clicking on the <K> or <S> symbol respectively. These are located in the _Action_ column.

Finally, you can quit this program by pressing either <q> or <C-c>


Terms frequency usage
---------------------

In AIL, you can track terms, set of terms and even regexes without creating a dedicated module. To do so, go to the tab `Terms Frequency` in the web interface.
- You can track a term by simply putting it in the box.
- You can track a set of terms by simply putting terms in an array surrounded by the '\' character. You can also set a custom threshold regarding the number of terms that must match to trigger the detection. For example, if you want to track the terms _term1_ and _term2_ at the same time, you can use the following rule: `\[term1, term2, [100]]\`
- You can track regexes as easily as tracking a term. You just have to put your regex in the box surrounded by the '/' character. For example, if you want to track the regex matching all email address having the domain _domain.net_, you can use the following aggressive rule: `/*.domain.net/`.

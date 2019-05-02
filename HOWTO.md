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

5. Launch pystemon-feeder ``` ./bin/feeder/pystemon-feeder.py ```


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


Terms frequency usage
---------------------

In AIL, you can track terms, set of terms and even regexes without creating a dedicated module. To do so, go to the tab `Terms Frequency` in the web interface.
- You can track a term by simply putting it in the box.
- You can track a set of terms by simply putting terms in an array surrounded by the '\' character. You can also set a custom threshold regarding the number of terms that must match to trigger the detection. For example, if you want to track the terms _term1_ and _term2_ at the same time, you can use the following rule: `\[term1, term2, [100]]\`
- You can track regexes as easily as tracking a term. You just have to put your regex in the box surrounded by the '/' character. For example, if you want to track the regex matching all email address having the domain _domain.net_, you can use the following aggressive rule: `/*.domain.net/`.


Crawler
---------------------

In AIL, you can crawl Tor hidden services. Don't forget to review the proxy configuration of your Tor client and especially if you enabled the SOCKS5 proxy and binding on the appropriate IP address reachable via the dockers where Splash runs.

There are two types of installation. You can install a *local* or a *remote* Splash server.
``(Splash host) = the server running the splash service``
``(AIL host) = the server running AIL``

### Installation/Configuration

1. *(Splash host)* Launch ``crawler_hidden_services_install.sh`` to install all requirements (type ``y`` if a localhost splah server is used or use the ``-y`` option)

2. *(Splash host)* To install and setup your tor proxy:
    - Install the tor proxy: ``sudo apt-get install tor -y``
        (Not required if ``Splah host == AIL host`` - The tor proxy is installed by default in AIL)

        (Warning: Some v3 onion address are not resolved with the tor proxy provided via apt get. Use the tor proxy provided by [The torproject](https://2019.www.torproject.org/docs/debian) to solve this issue)
    - Allow Tor to bind to any interface or to the docker interface (by default binds to 127.0.0.1 only) in ``/etc/tor/torrc``
        ``SOCKSPort 0.0.0.0:9050`` or
        ``SOCKSPort 172.17.0.1:9050``
    - Add the following line ``SOCKSPolicy accept 172.17.0.0/16`` in ``/etc/tor/torrc``
      (for a linux docker, the localhost IP is *172.17.0.1*; Should be adapted for other platform)
    - Restart the tor proxy: ``sudo service tor restart``

3. *(AIL host)* Edit the ``/bin/packages/config.cfg`` file:
    - In the crawler section, set ``activate_crawler`` to ``True``
    - Change the IP address of Splash servers if needed (remote only)
    - Set ``splash_onion_port`` according to your Splash servers port numbers that will be used.
        those ports numbers should be described as a single port (ex: 8050) or a port range (ex: 8050-8052 for 8050,8051,8052 ports).


### Starting the scripts

- *(Splash host)* Launch all Splash servers with:
```sudo ./bin/torcrawler/launch_splash_crawler.sh -f <config absolute_path> -p <port_start> -n <number_of_splash>```
With ``<port_start>`` and ``<number_of_splash>`` matching those specified at ``splash_onion_port`` in the configuration file of point 3 (``/bin/packages/config.cfg``)

All Splash dockers are launched inside the ``Docker_Splash`` screen. You can use ``sudo screen -r Docker_Splash`` to connect to the screen session and check all Splash servers status.

- (AIL host) launch all AIL crawler scripts using:
```./bin/LAUNCH.sh -c```


### TL;DR - Local setup

#### Installation
- ```crawler_hidden_services_install.sh -y```
- Add the following line in ``SOCKSPolicy accept 172.17.0.0/16`` in ``/etc/tor/torrc``
- ```sudo service tor restart```
- set activate_crawler to True in ``/bin/packages/config.cfg``
#### Start
- ```sudo ./bin/torcrawler/launch_splash_crawler.sh -f $AIL_HOME/configs/docker/splash_onion/etc/splash/proxy-profiles/ -p 8050 -n 1```

If AIL framework is not started, it's required to start it before the crawler service:

- ```./bin/LAUNCH.sh -l```

Then starting the crawler service (if you follow the procedure above)

- ```./bin/LAUNCH.sh -c```

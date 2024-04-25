
# Feeding, Adding new features and Contributing

## [AIL Importers](./doc/README.md#ail-importers)

Refer to the [AIL Importers Documentation](./doc/README.md#ail-importers)

## Feeding Data to AIL

AIL is an analysis tool, not a collector!
However, if you want to collect some pastes and feed them to AIL, the procedure is described below. Nevertheless, moderate your queries!

1. [AIL Importers](./doc/README.md#ail-importers)
2. ZMQ: Be a collaborator of CIRCL and ask to access our feed. It will be sent to the static IP you are using for AIL.

## How to create a new module

To add a new processing or analysis module to AIL, follow these steps:

1. Add your module name in [./configs/modules.cfg](./configs/modules.cfg) and subscribe to at least one module at minimum (Usually, `Item`).
2. Use [./bin/modules/modules/TemplateModule.py](./bin/modules/modules/TemplateModule.py) as a sample module and create a new file in bin/modules with the module name used in the `modules.cfg` configuration.


## Contributions

Contributions are welcome! Fork the repository, experiment with the code, and submit your modules or patches through a pull request.

## Crawler

AIL supports crawling of websites and Tor hidden services. Ensure your Tor client's proxy configuration is correct, especially the SOCKS5 proxy settings.

![Crawler](./doc/screenshots/ail-lacus.png?raw=true "AIL framework Crawler")

### Installation

[Install Lacus](https://github.com/ail-project/lacus)

### Configuration

1. Lacus URL:  
In the web interface, go to `Crawlers` > `Settings` and click on the Edit button

![AIL Crawler Config](./doc/screenshots/lacus_config.png?raw=true "AIL Lacus Config")

![AIL Crawler Config Edis](./doc/screenshots/lacus_config_edit.png?raw=true "AIL Lacus Config")

2. Number of Crawlers:
Choose the number of crawlers you want to launch

![Crawler Manager Nb Crawlers Config](./doc/screenshots/crawler_nb_captures.png?raw=true "AIL Lacus Nb Crawlers Config")

![Crawler Manager Nb Crawlers Config](./doc/screenshots/crawler_nb_captures_edit.png?raw=true "AIL Lacus Nb Crawlers Config")

## Chats Translation with LibreTranslate

Chats message can be translated using [libretranslate](https://github.com/LibreTranslate/LibreTranslate), an open-source self-hosted machine translation.

### Installation:  
1. Install LibreTranslate by running the following command:
```bash
pip install libretranslate
```
2. Run libretranslate:
```bash
libretranslate
```

### Configuration:
To enable LibreTranslate for chat translation, edit the LibreTranslate URL in the [./configs/core.cfg](./configs/core.cfg) file under the [Translation] section.
```
[Translation]
libretranslate = http://127.0.0.1:5000
```


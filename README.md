# AIL framework

<img src="https://raw.githubusercontent.com/ail-project/ail-framework/master/var/www/static/image/ail-icon.png" height="400" />

<table>
<tr>
  <td>Latest Release</td>
  <td><a href="https://github.com/ail-project/ail-framework/releases/latest"><img src="https://img.shields.io/github/release/ail-project/ail-framework/all.svg"></a></td>
</tr>
<tr>
  <td>CI</td>
  <td><a href="https://github.com/ail-project/ail-framework/actions/workflows/ail_framework_test.yml"><img src="https://github.com/ail-project/ail-framework/actions/workflows/ail_framework_test.yml/badge.svg"></a></td>
</tr>
<tr>
  <td>Gitter</td>
  <td><a href="https://gitter.im/ail-project/?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge"><img src="https://badges.gitter.im/ail-project.svg" /></a></td>
</tr>
<tr>
  <td>Contributors</td>
  <td><img src="https://img.shields.io/github/contributors/ail-project/ail-framework.svg" /></td>
</tr>
<tr>
  <td>License</td>
  <td><img src="https://img.shields.io/github/license/ail-project/ail-framework.svg" /></td>
</tr>
</table>

AIL framework - Framework for Analysis of Information Leaks

AIL is a modular framework to analyse potential information leaks from unstructured data sources like pastes from Pastebin or similar services or unstructured data streams. AIL framework is flexible and can be extended to support other functionalities to mine or process sensitive information (e.g. data leak prevention).

![Overview](https://www.ail-project.org/assets/img/dashboard.jpeg "AIL framework Dashboard")


![Finding webshells with AIL](./doc/screenshots/webshells.gif?raw=true "Finding webshells with AIL")

## AIL V5.0 Version:

AIL v5.0 introduces significant improvements and new features:

- **Codebase Rewrite**: The codebase has undergone a substantial rewrite, 
resulting in enhanced performance and speed improvements.
- **Database Upgrade**: The database has been migrated from ARDB to Kvrocks.
- **New Correlation Engine**: AIL v5.0 introduces a new powerful correlation engine with two new correlation types: CVE and Title.
- **Enhanced Logging**: The logging system has been improved to provide better troubleshooting capabilities.
- **Tagging Support**: [AIL objects](./doc/README.md#ail-objects) now support tagging, 
allowing users to categorize and label extracted information for easier analysis and organization.
- **Trackers**: Improved objects filtering, PGP and decoded tracking added.
- **UI Content Visualization**: The user interface has been upgraded to visualize extracted and tracked information.
- **New Crawler Lacus**: improve crawling capabilities.
- **Modular Importers and Exporters**: New importers (ZMQ, AIL Feeders) and exporters (MISP, Mail, TheHive) modular design.
Allow easy creation and customization by extending an abstract class.
- **Module Queues**: improved the queuing mechanism between detection modules.
- **New Object CVE and Title**: Extract an correlate CVE IDs and web page titles.

## Features

![Internal](./doc/screenshots/ail-internal.png?raw=true "AIL framework Internal")

- Modular architecture to handle streams of unstructured or structured information
- Default support for external ZMQ feeds, such as provided by CIRCL or other providers
- Multiple Importers and feeds support
- Each module can process and reprocess the information already analyzed by AIL
- Detecting and extracting URLs including their geographical location (e.g. IP address location)
- Extracting and validating potential leaks of credit card numbers, credentials, ...
- Extracting and validating leaked email addresses, including DNS MX validation
- Module for extracting Tor .onion addresses for further analysis
- Keep tracks of credentials duplicates (and diffing between each duplicate found)
- Extracting and validating potential hostnames (e.g. to feed Passive DNS systems)
- A full-text indexer module to index unstructured information
- Terms, Set of terms, Regex, typo squatting and YARA tracking and occurrence
- YARA Retro Hunt
- Many more modules for extracting phone numbers, credentials, and more
- Alerting to [MISP](https://github.com/MISP/MISP) to share found leaks within a threat intelligence platform using [MISP standard](https://www.misp-project.org/objects.html#_ail_leak)
- Detecting and decoding encoded file (Base64, hex encoded or your own decoding scheme) and storing files
- Detecting Amazon AWS and Google API keys
- Detecting Bitcoin address and Bitcoin private keys
- Detecting private keys, certificate, keys (including SSH, OpenVPN)
- Detecting IBAN bank accounts
- Tagging system with [MISP Galaxy](https://github.com/MISP/misp-galaxy) and [MISP Taxonomies](https://github.com/MISP/misp-taxonomies) tags
- UI submission
- Create events on [MISP](https://github.com/MISP/MISP) and cases on [The Hive](https://github.com/TheHive-Project/TheHive)
- Automatic export on detection with [MISP](https://github.com/MISP/MISP) (events) and [The Hive](https://github.com/TheHive-Project/TheHive) (alerts) on selected tags
- Extracted and decoded files can be searched by date range, type of file (mime-type) and encoding discovered
- Correlations engine and Graph to visualize relationships between decoded files (hashes), PGP UIDs, domains, username, and cryptocurrencies addresses
- Websites, Forums and Tor Hidden-Services hidden services crawler to crawl and parse output
- Domain availability monitoring to detect up and down of websites and hidden services
- Browsed hidden services are automatically captured and integrated into the analyzed output, including a blurring screenshot interface (to avoid "burning the eyes" of security analysts with sensitive content)
- Tor hidden services is part of the standard framework, all the AIL modules are available to the crawled hidden services
- Crawler scheduler to trigger crawling on demand or at regular intervals for URLs or Tor hidden services


## Installation

To install the AIL framework, run the following commands:
```bash
# Clone the repo first
git clone https://github.com/ail-project/ail-framework.git
cd ail-framework

# For Debian and Ubuntu based distributions
./installing_deps.sh

# Launch ail
cd ~/ail-framework/
cd bin/
./LAUNCH.sh -l
```

The default [installing_deps.sh](./installing_deps.sh) is for Debian and Ubuntu based distributions.

Requirement:
- Python 3.8+

## Installation Notes

For Lacus Crawler and LibreTranslate installation instructions (if you want to use those features), refer to the [HOWTO](https://github.com/ail-project/ail-framework/blob/master/HOWTO.md#crawler)

## Starting AIL

To start AIL, use the following commands:

```bash
cd bin/
./LAUNCH.sh -l
```
You can access the AIL framework web interface at the following URL: 

```
https://localhost:7000/
```

The default credentials for the web interface are located in the ``DEFAULT_PASSWORD``file, which is deleted when you change your password.

## Training

CIRCL organises training on how to use or extend the AIL framework. AIL training materials are available at [https://github.com/ail-project/ail-training](https://github.com/ail-project/ail-training).


## API

The API documentation is available in [doc/api.md](doc/api.md)

## HOWTO

HOWTO are available in [HOWTO.md](HOWTO.md)

## Privacy and GDPR

For information on AIL's compliance with GDPR and privacy considerations, refer to the [AIL information leaks analysis and the GDPR in the context of collection, analysis and sharing information leaks](https://www.circl.lu/assets/files/information-leaks-analysis-and-gdpr.pdf) document.

this document provides an overview how to use AIL in a lawfulness context especially in the scope of General Data Protection Regulation.

## Research using AIL

If you use or reference AIL in an academic paper, you can cite it using the following BibTeX:

~~~~
@inproceedings{mokaddem2018ail,
  title={AIL-The design and implementation of an Analysis Information Leak framework},
  author={Mokaddem, Sami and Wagener, G{\'e}rard and Dulaunoy, Alexandre},
  booktitle={2018 IEEE International Conference on Big Data (Big Data)},
  pages={5049--5057},
  year={2018},
  organization={IEEE}
}
~~~~

## Screenshots

### Websites, Forums and Tor Hidden-Services

![Domain CIRCL](./doc/screenshots/domain_circl.png?raw=true "Tor hidden service crawler")

#### Login protected, pre-recorded session cookies:
![Domain cookiejar](./doc/screenshots/crawler-cookiejar-domain-crawled.png?raw=true "Tor hidden service crawler")

### Extracted encoded files from items

![Extracted files](./doc/screenshots/decodeds_dashboard.png?raw=true "AIL extracted decoded files statistics")

### Correlation Engine

![Correlation decoded image](./doc/screenshots/correlation_decoded_image.png?raw=true "Correlation decoded image")

### Investigation

![Investigation](./doc/screenshots/investigation_mixer.png?raw=true "AIL framework cookiejar")

### Tagging system

![Tags](./doc/screenshots/tags_search.png?raw=true "AIL framework tags")

![Tags search](./doc/screenshots/tags_search_items.png?raw=true "AIL framework tags items search")

### MISP Export

![misp_export](./doc/screenshots/misp_export.png?raw=true "AIL framework MISP Export")

### MISP and The Hive, automatic events and alerts creation

![tags_misp_auto](./doc/screenshots/tags_misp_auto.png?raw=true "AIL framework MISP and Hive auto export")

### UI submission

![ui_submit](./doc/screenshots/ui_submit.png?raw=true "AIL framework UI importer")

### Trackers

![tracker-create](./doc/screenshots/tracker_create.png?raw=true "AIL framework create tracker")

![tracker-yara](./doc/screenshots/tracker_yara.png?raw=true "AIL framework Yara tracker")

![retro-hunt](./doc/screenshots/retro_hunt.png?raw=true "AIL framework Retro Hunt")

## License

```
    Copyright (C) 2014 Jules Debra
    Copyright (c) 2021 Olivier Sagit
    Copyright (C) 2014-2024 CIRCL - Computer Incident Response Center Luxembourg (c/o smile, security made in Lëtzebuerg, Groupement d'Intérêt Economique)
    Copyright (c) 2014-2024 Raphaël Vinot
    Copyright (c) 2014-2024 Alexandre Dulaunoy
    Copyright (c) 2016-2024 Sami Mokaddem
    Copyright (c) 2018-2024 Thirion Aurélien

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

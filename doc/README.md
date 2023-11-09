

# AIL objects

AIL is using different types of objects to classify, correlate and describe extracted information:

- **Cryptocurrency**: Represents extracted cryptocurrency addresses.
    - bitcoin
    - bitcoin-cash
    - dash
    - ethereum
    - litecoin
    - monero
    - zcash
- **Cve**: Represents extracted CVE (Common Vulnerabilities and Exposures) IDs.
- **Decoded**: Represents information that has been decoded from an encoded format, such as base64.
- **Domain**: Represents crawled domains and includes metadata related to them.
- **Item**: Represents a piece of text that has been processed by AIL. It can include various types of extracted information.
- **Pgp**: Represents PGP key/block metadata.
    - key: PGP key IDs
    - mail: email addresses associated with PGP keys
    - name: names associated with PGP keys.
- **Screenshot**: Represents screenshots captured from crawled domains.
- **Title**: Represents the HTML title extracted from web pages.
- **Username**:
    - telegram: telegram username handles
    - twitter: twitter username handles
    - jabber: Jabber (XMPP) username handles


# AIL Importers

AIL Importers play a crucial role in the AIL ecosystem, 
enabling the import of various types of data into the framework. 

These importers are located in the `/bin/importer` directory.
The modular design of importers allows for easy expansion and customization, 
ensuring that AIL can adapt to new types of data.

Available Importers:
- [AIL Feeders](#ail-feeders): Extract and feed JSON data from external sources via The API.
- ZMQ
- [pystemon](https://github.com/cvandeplas/pystemon)
- File: Import files and directories.
(Manually Feed File/Dir: [./tool/file_dir_importer.py](./tool/file_dir_importer.py)).

[//]: # (### ZMQ Importer:)

### pystemon:

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
		 ./ail-framework/bin/LAUNCH.sh -l #starts ail-framework
		 ./ail-framework/bin/LAUNCH.sh -f #starts pystemon and the PystemonImporter.py
		```
     - Option 2 (may require two terminal windows): 
        ``` 
        ./ail-framework/bin/LAUNCH.sh -l #starts ail-framework
        ./pystemon/pystemon.py
        ./ail-framework/bin/importer/PystemonImporter.py
        ```

### File Importer `importer/FileImporter.py`:

Manually import File and Directory with the [./tool/file_dir_importer.py](./tool/file_dir_importer.py) script:

- Import Files:
  ```shell
  . ./AILENV/bin/activate
  cd tools/
  ./file_dir_importer.py -f MY_FILE_PAT
  ```
  
- Import Dirs:
  ```shell
  . ./AILENV/bin/activate
  cd tools/
  ./file_dir_importer.py -d MY_DIR_PATH
  ```

### Create a New Importer:

```python
from importer.abstract_importer import AbstractImporter
from modules.abstract_module import AbstractModule

class MyNewImporter(AbstractImporter):

    def __init__(self):
        super().__init__()
        # super().__init__(queue=True)   # if it's an one-time run importer
        self.logger.info(f'Importer {self.name} initialized')

    def importer(self, my_var):
        # Process my_var and get content to import
        content = GET_MY_CONTENT_TO_IMPORT
        # if content is not gzipped and/or not b64 encoded,
        # set gzipped and/or b64 to False
        message = self.create_message(item_id, content, b64=False, gzipped=False)
        return message
        # if it's an one-time run, otherwise create an AIL Module
        # self.add_message_to_queue(message)

class MyNewModuleImporter(AbstractModule):
    def __init__(self):
        super().__init__()
        # init module ...
        self.importer = MyNewImporter()

    def get_message(self):
        return self.importer.importer()

    def compute(self, message):
        self.add_message_to_queue(message)

if __name__ == '__main__':
    module = MyNewModuleImporter()
    module.run()

    # if it's an one-time run:
    # importer = MyImporter()
    # importer.importer(my_var)
```

## AIL Feeders

AIL Feeders are a special type of Importer within AIL, specifically designed 
to *extract* and *feed* data from external sources into the framework.

- **Extract Data**: AIL Feeders extract data from external sources, such as APK files, 
certificate transparency logs, GitHub archives, repositories, ActivityPub sources, 
leaked files, Atom/RSS feeds, JSON logs, Discord, and Telegram, ...
- **Run Independently**: Feeders can run on separate systems or infrastructure, 
providing flexibility and scalability. They operate independently from the core AIL framework.
- **Internal Logic**: Each feeder can implement its own custom logic and processing 
to extract and transform data and metadata from the source into JSON.
- **Push to AIL API**: The generated JSON is then pushed to the AIL API 
for ingestion and further analysis within the AIL framework.

[//]: # (- Customize medata parsing)


### AIL Feeders List:
- [ail-feeder-apk](https://github.com/ail-project/ail-feeder-apk): Pushes annotated APK to an AIL instance for yara detection.
- [ail-feeder-ct](https://github.com/ail-project/ail-feeder-ct): AIL feeder for certificate transparency.
- [ail-feeder-github-gharchive](https://github.com/ail-project/ail-feeder-gharchive): extract informations 
from GHArchive, collect and feed AIL
- [ail-feeder-github-repo](https://github.com/ail-project/ail-feeder-github-repo): Pushes github repositories to AIL.
- [ail-feeder-activity-pub](https://github.com/ail-project/ail-feeder-activity-pub) ActivityPub feeder.
- [ail-feeder-leak](https://github.com/ail-project/ail-feeder-leak): Automates the process of feeding files to AIL, using data chunking to handle large files.
- [ail-feeder-atom-rss](https://github.com/ail-project/ail-feeder-atom-rss) Atom and RSS feeder for AIL.
- [ail-feeder-jsonlogs](https://github.com/ail-project/ail-feeder-jsonlogs) Aggregate JSON log lines and pushes them  to AIL. 
- [ail-feeder-discord](https://github.com/ail-project/ail-feeder-discord) Discord Feeder.
- [ail-feeder-telegram](https://github.com/ail-project/ail-feeder-telegram) Telegram Channels and User Feeder.

#### Example: Feeding AIL with Conti leaks

```python
from pyail import PyAIL
pyail = PyAIL(URL, API_KEY, ssl=verifycert)

#. . . imports
#. . . setup code

for elem in sys.stdin:
    elm = json.loads(elem)
    content = elm['body']
    meta = {}
    meta['jabber:to'] = elm['to']
    meta['jabber:from'] = elm['from']
    meta['jabber:ts]' = elm['ts']
    pyail.feed_json_item(content , meta, feeder_name, feeder_uuid)
```

# AIL SYNC

The synchronisation mechanism allow the sync from one AIL instance to another AIL using a standard WebSocket 
using [AIL JSON protocol](https://github.com/ail-project/ail-exchange-format/blob/main/ail-stream.md). 
The synchronisation allows to filter and sync specific collected items including crawled items or 
specific tagged items matching defined rules. 
This feature can be very useful to limit the scope of analysis in specific fields or resource intensive activity. 
This sync can be also used to share filtered streams with other partners.



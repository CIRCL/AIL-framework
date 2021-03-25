Overview
========

Redis and ARDB overview
--------------------------

* Redis on TCP port 6379
    - DB 0 - Cache hostname/dns
    - DB 1 - Paste meta-data
* Redis on TCP port 6380 - Redis Log only
* Redis on TCP port 6381
    - DB 0 - PubSub + Queue and Paste content LRU cache
    - DB 1 - _Mixer_ Cache
* ARDB on TCP port 6382


     DB 1 - Curve
     DB 2 - TermFreq
     DB 3 - Trending/Trackers
     DB 4 - Sentiments
     DB 5 - TermCred
     DB 6 - Tags
     DB 7 - Metadata
     DB 8 - Statistics
     DB 9 - Crawler
     DB 10 - Objects

* ARDB on TCP port <year>
    - DB 0 - Lines duplicate
    - DB 1 - Hashes

# Database Map:

### Redis cache

##### Brute force protection:
| Set Key | Value |
| ------ | ------ |
| failed_login_ip:**ip**           | **nb login failed** | TTL
| failed_login_user_id:**user_id** | **nb login failed** | TTL

##### Item Import:

| Key | Value |
| ------ | ------ |
| **uuid**:nb_total   | **nb total**      | TTL *(if imported)*
| **uuid**:nb_end     | **nb**            | TTL *(if imported)*
| **uuid**:nb_sucess  | **nb success**    | TTL *(if imported)*
| **uuid**:end        | **0 (in progress) or (item imported)** | TTL *(if imported)*
| **uuid**:processing | **process status: 0 or 1**             | TTL *(if imported)*
| **uuid**:error      | **error message** | TTL *(if imported)*

| Set Key | Value |
| ------ | ------ |
| **uuid**:paste_submit_link | **item_path** | TTL *(if imported)*

## DB0 - Core:

##### Update keys:
| Key | Value |
| ------ | ------ |
| | |
| ail:version | **current version** |
| | |
| ail:update_**update_version** | **background update name** |
| | **background update name** |
| | **...** |
| | |
| ail:update_error | **update message error** |
| | |
| ail:update_in_progress | **update version in progress** |
| ail:current_background_update | **current update version** |
| | |
| ail:current_background_script | **name of the background script currently executed** |
| ail:current_background_script_stat | **progress in % of the background script** |

| Hset Key | Field | Value |
| ------ | ------ | ------ |
| ail:update_date | **update tag** | **update date**  |

##### User Management:
| Hset Key | Field | Value |
| ------ | ------ | ------ |
| user:all | **user id** | **password hash**  |
| | | |
| user:tokens | **token** | **user id** |
| | | |
| user_metadata:**user id** | token | **token**  |
|                           | change_passwd  | **boolean** |
|                           | role  | **role** |

| Set Key | Value |
| ------ | ------ |
| user_role:**role** | **user id** |


| Zrank Key | Field | Value |
| ------ | ------ | ------ |
| ail:all_role | **role** | **int, role priority (1=admin)** |

##### MISP Modules:

| Set Key | Value |
| ------ | ------ |
| enabled_misp_modules | **module name** |

| Key | Value |
| ------ | ------ |
| misp_module:**module name** | **module dict** |

##### Item Import:
| Key | Value |
| ------ | ------ |
| **uuid**:isfile   | **boolean** |
| **uuid**:paste_content | **item_content** |

## DB2 - TermFreq:

| Set Key | Value |
| ------ | ------ |
| submitted:uuid | **uuid** |
| **uuid**:ltags | **tag** |
| **uuid**:ltagsgalaxies | **tag** |

## DB3 - Leak Hunter:

##### Tracker metadata:
| Hset - Key | Field | Value |
| ------ | ------ | ------ |
| tracker:**uuid**      | tracker     | **tacked word/set/regex**          |
|                       | type        | **word/set/regex**                 |
|                       | date        | **date added**                     |
|                       | user_id     | **created by user_id**             |
|                       | dashboard   | **0/1 Display alert on dashboard** |
|                       | description | **Tracker description**            |
|                       | level       | **0/1 Tracker visibility**         |

##### Tracker by user_id (visibility level: user only):
| Set - Key | Value |
| ------ | ------ |
| user:tracker:**user_id** | **uuid - tracker uuid** |
| user:tracker:**user_id**:**word/set/regex - tracker type** | **uuid - tracker uuid** |

##### Global Tracker (visibility level: all users):
| Set - Key | Value |
| ------ | ------ |
| gobal:tracker | **uuid - tracker uuid** |
| gobal:tracker:**word/set/regex - tracker type** | **uuid - tracker uuid** |

##### All Tracker by type:
| Set - Key | Value |
| ------ | ------ |
| all:tracker:**word/set/regex - tracker type** | **tracked item** |

| Set - Key | Value |
| ------ | ------ |
| all:tracker_uuid:**tracker type**:**tracked item** | **uuid - tracker uuid** |

##### All Tracked items:
| Set - Key | Value |
| ------ | ------ |
| tracker:item:**uuid**:**date** | **item_id** |

##### All Tracked tags:
| Set - Key | Value |
| ------ | ------ |
| tracker:tags:**uuid** | **tag** |

##### All Tracked mail:
| Set - Key | Value |
| ------ | ------ |
| tracker:mail:**uuid** | **mail** |

##### Refresh Tracker:
| Key | Value |
| ------ | ------ |
| tracker:refresh:word | **last refreshed epoch** |
| tracker:refresh:set | - |
| tracker:refresh:regex | - |

##### Zset Stat Tracker:
| Key | Field | Value |
| ------ | ------ | ------ |
| tracker:stat:**uuid** | **date** | **nb_seen** |

##### Stat token:
| Key | Field | Value |
| ------ | ------ | ------ |
| stat_token_total_by_day:**date** | **word** | **nb_seen** |
| | | |
| stat_token_per_item_by_day:**date** | **word** | **nb_seen** |

| Set - Key | Value |
| ------ | ------ |
| stat_token_history | **date** |

## DB6 - Tags:

##### Hset:
| Key | Field | Value |
| ------ | ------ | ------ |
| tag_metadata:**tag** | first_seen | **date** |
| tag_metadata:**tag** | last_seen | **date** |

##### Set:
| Key | Value |
| ------ | ------ |
| list_tags | **tag** |
| list_tags:**object_type** | **tag** |
| list_tags:domain | **tag** |
||
| active_taxonomies | **taxonomie** |
| active_galaxies | **galaxie** |
| active_tag_**taxonomie or galaxy** | **tag** |
| synonym_tag_misp-galaxy:**galaxy** | **tag synonym** |
| list_export_tags | **user_tag** |
||
| **tag**:**date** | **paste** |
| **object_type**:**tag** | **object_id** |
||
| DB7 |
| tag:**object_id** | **tag** |

##### old:
| Key | Value |
| ------ | ------ |
| *tag* | *paste* |

## DB7 - Metadata:

#### Crawled Items:
##### Hset:
| Key | Field | Value |
| ------ | ------ | ------ |
| paste_metadata:**item path** | super_father | **first url crawled** |
| | father | **item father** |
| | domain | **crawled domain**:**domain port** |
| | screenshot | **screenshot hash** |

##### Set:
| Key | Field |
| ------ | ------ |
| tag:**item path** | **tag** |
| | |
| paste_children:**item path** | **item path** |
| | |
| hash_paste:**item path** | **hash** |
| base64_paste:**item path** | **hash** |
| hexadecimal_paste:**item path** | **hash** |
| binary_paste:**item path** | **hash** |

##### Zset:
| Key | Field | Value |
| ------ | ------ | ------ |
| nb_seen_hash:**hash** | **item** | **nb_seen** |
| base64_hash:**hash** | **item** | **nb_seen** |
| binary_hash:**hash** | **item** | **nb_seen** |
| hexadecimal_hash:**hash** | **item** | **nb_seen** |

#### PgpDump

##### Hset:
| Key | Field | Value |
| ------ | ------ | ------ |
| pgpdump_metadata_key:*key id* | first_seen | **date** |
| | last_seen | **date** |
| | |
| pgpdump_metadata_name:*name* | first_seen | **date** |
| | last_seen | **date** |
| | |
| pgpdump_metadata_mail:*mail* | first_seen | **date** |
| | last_seen | **date** |

##### set:
| Key | Value |
| ------ | ------ |
| set_pgpdump_key:*key id* | *item_path* |
| | |
| set_pgpdump_name:*name* | *item_path* |
| | |
| set_pgpdump_mail:*mail* | *item_path* |
| | |
| | |
| set_domain_pgpdump_**pgp_type**:**key** | **domain** |

##### Hset date:
| Key | Field | Value |
| ------ | ------ |
| pgpdump:key:*date* | *key* | *nb seen* |
| | |
| pgpdump:name:*date* | *name* | *nb seen* |
| | |
| pgpdump:mail:*date* | *mail* | *nb seen* |

##### zset:
| Key | Field | Value |
| ------ | ------ | ------ |
| pgpdump_all:key | *key* | *nb seen* |
| | |
| pgpdump_all:name | *name* | *nb seen* |
| | |
| pgpdump_all:mail | *mail* | *nb seen* |

##### set:
| Key | Value |
| ------ | ------ |
| item_pgpdump_key:*item_path* | *key* |
| | |
| item_pgpdump_name:*item_path* | *name* |
| | |
| item_pgpdump_mail:*item_path* | *mail* |
| | |
| | |
| domain_pgpdump_**pgp_type**:**domain** | **key** |

#### SimpleCorrelation:
##### zset:
| Key | Field | Value |
| ------ | ------ | ------ |
| s_correl:*correlation name*:all | *object_id* | *nb_seen* |
| s_correl:date:*correlation name*:*date_day* | *object_id* | *nb_seen |

##### set:
| Key | Value |
| ------ | ------ |
| s_correl:set_*object type*_*correlation name*:*object_id* | *item_id* |
| *object type*:s_correl:*correlation name*:*object_id* | *correlation_id* |

object type: item + domain

##### hset:
| Key | Field | Value |
| ------ | ------ | ------ |
| 's_correl:*correlation name*:metadata:*obj_id* | first_seen | *first_seen* |
| 's_correl:*correlation name*:metadata:*obj_id* | last_seen | *last_seen* |

#### Cryptocurrency

Supported cryptocurrency:
- bitcoin
- bitcoin-cash
- dash
- etherum
- litecoin
- monero
- zcash

##### Hset:
| Key | Field | Value |
| ------ | ------ | ------ |
| cryptocurrency_metadata_**cryptocurrency name**:**cryptocurrency address** | first_seen | **date** |
| | last_seen | **date** |

##### set:
| Key | Value |
| ------ | ------ |
| set_cryptocurrency_**cryptocurrency name**:**cryptocurrency address** | **item_path** | PASTE
| domain_cryptocurrency_**cryptocurrency name**:**cryptocurrency address** | **domain** | DOMAIN

##### Hset date:
| Key | Field | Value |
| ------ | ------ |
| cryptocurrency:**cryptocurrency name**:**date** | **cryptocurrency address** | **nb seen** |

##### zset:
| Key | Field | Value |
| ------ | ------ | ------ |
| cryptocurrency_all:**cryptocurrency name** | **cryptocurrency address** | **nb seen** |

##### set:
| Key | Value |
| ------ | ------ |
| item_cryptocurrency_**cryptocurrency name**:**item_path** | **cryptocurrency address** | PASTE
| domain_cryptocurrency_**cryptocurrency name**:**item_path** | **cryptocurrency address** | DOMAIN

#### HASH
| Key | Value |
| ------ | ------ |
| hash_domain:**domain** | **hash** |
| domain_hash:**hash** | **domain** |

## DB9 - Crawler:

##### Hset:
| Key | Field | Value |
| ------ | ------ | ------ |
| **service type**_metadata:**domain** | first_seen | **date** |
| | last_check | **date** |
| | ports | **port**;**port**;**port** ... |
| | paste_parent | **parent last crawling (can be auto or manual)** |

##### Zset:
| Key | Field | Value |
| ------ | ------ | ------ |
| crawler\_history\_**service type**:**domain**:**port** | **item root (first crawled item)** | **epoch (seconds)** |

##### Set:
| Key | Value |
| ------ | ------ | ------ |
| screenshot:**sha256** | **item path** |

##### crawler config:
| Key | Value |
| ------ | ------ |
| crawler\_config:**crawler mode**:**service type**:**domain** | **json config** |

##### automatic crawler config:
| Key | Value |
| ------ | ------ |
| crawler\_config:**crawler mode**:**service type**:**domain**:**url** | **json config** |

###### exemple json config:
```json
{
  "closespider_pagecount": 1,
  "time": 3600,
  "depth_limit": 0,
  "har": 0,
  "png": 0
}
```

### Splash containers and proxies:
| SET - Key | Value |
| ------ | ------ |
| all_proxy  | **proxy name**  |
| all_splash | **splash name** |

| HSET - Key | Field | Value |
| ------ | ------ | ------ |
| proxy:metadata:**proxy name** | host         | **host**              |
| proxy:metadata:**proxy name** | port         | **port**              |
| proxy:metadata:**proxy name** | type         | **type**              |
| proxy:metadata:**proxy name** | crawler_type | **crawler_type**      |
| proxy:metadata:**proxy name** | description  | **proxy description** |
|  |  |  |
| splash:metadata:**splash name** | description  | **splash description**          |
| splash:metadata:**splash name** | crawler_type | **crawler_type**                |
| splash:metadata:**splash name** | proxy        | **splash proxy (None if null)** |

| SET - Key | Value |
| ------ | ------ |
| splash:url:**container name** | **splash url**     |
| proxy:splash:**proxy name**   | **container name** |

|  Key | Value |
| ------ | ------ |
| splash:map:url:name:**splash url** | **container name** |

##### CRAWLER QUEUES:
| SET - Key | Value |
| ------ | ------ |
| onion_crawler_queue | **url**;**item_id** | RE-CRAWL
| regular_crawler_queue | - |
|  |  |
| onion_crawler_priority_queue   | **url**;**item_id** | USER
| regular_crawler_priority_queue | - |
|  |  |
| onion_crawler_discovery_queue   | **url**;**item_id** | DISCOVER
| regular_crawler_discovery_queue | - |

##### TO CHANGE:

ARDB overview

	----------------------------------------- SENTIMENT ------------------------------------

	SET - 'Provider_set'				Provider

	KEY - 'UniqID' 					INT

	SET - provider_timestamp			UniqID

	SET - UniqID					avg_score



* DB 7 - Metadata:


	----------------------------------------------------------------------------------------
	----------------------------------------- BASE64 ----------------------------------------

	HSET - 'metadata_hash:'+hash	'saved_path'		saved_path
					'size'			size
					'first_seen'		first_seen
					'last_seen'		last_seen
					'estimated_type'	estimated_type
					'vt_link'		vt_link
					'vt_report'		vt_report
					'nb_seen_in_all_pastes'	nb_seen_in_all_pastes
					'base64_decoder'	nb_encoded
					'binary_decoder'	nb_encoded

	SET  - 'all_decoder'		decoder*

	SET  - 'hash_all_type'		hash_type *
	SET  - 'hash_base64_all_type'	hash_type *
	SET  - 'hash_binary_all_type'	hash_type *

	ZADD - 'hash_date:'+20180622	hash *			nb_seen_this_day
	ZADD - 'base64_date:'+20180622	hash *			nb_seen_this_day
	ZADD - 'binary_date:'+20180622	hash *			nb_seen_this_day

	ZADD - 'base64_type:'+type	date			nb_seen
	ZADD - 'binary_type:'+type	date			nb_seen

	GET  - 'base64_decoded:'+date	nd_decoded
	GET  - 'binary_decoded:'+date	nd_decoded

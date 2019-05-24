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
     DB 3 - Trending
     DB 4 - Sentiments
     DB 5 - TermCred
     DB 6 - Tags
     DB 7 - Metadata
     DB 8 - Statistics
     DB 9 - Crawler

* ARDB on TCP port <year>
    - DB 0 - Lines duplicate
    - DB 1 - Hashes

# Database Map:

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
| ail:update_date_v1.5 | **update date** |
| | |
| ail:update_error | **update message error** |
| | |
| ail:update_in_progress | **update version in progress** |
| ail:current_background_update | **current update version** |
| | |
| ail:current_background_script | **name of the background script currently executed** |
| ail:current_background_script_stat | **progress in % of the background script** |

## DB2 - TermFreq:

##### Set:
| Key | Value |
| ------ | ------ |
| TrackedSetTermSet | **tracked_term** |
| TrackedSetSet | **tracked_set** |
| TrackedRegexSet | **tracked_regex** |
| | |
| tracked_**tracked_term** | **item_path** |
| set_**tracked_set** | **item_path** |
| regex_**tracked_regex** | **item_path** |
| | |
| TrackedNotifications | **tracked_trem / set / regex** |
| | |
| TrackedNotificationTags_**tracked_trem / set / regex** | **tag** |
| | |
| TrackedNotificationEmails_**tracked_trem / set / regex** | **email** |

##### Zset:
| Key | Field | Value |
| ------ | ------ | ------ |
| per_paste_TopTermFreq_set_month | **term** | **nb_seen** |
| per_paste_TopTermFreq_set_week | **term** | **nb_seen** |
| per_paste_TopTermFreq_set_day_**epoch** | **term** | **nb_seen** |
| | | |
| TopTermFreq_set_month | **term** | **nb_seen** |
| TopTermFreq_set_week | **term** | **nb_seen** |
| TopTermFreq_set_day_**epoch** | **term** | **nb_seen** |


##### Hset:
| Key | Field | Value |
| ------ | ------ | ------ |
| TrackedTermDate | **tracked_term** | **epoch** |
| TrackedSetDate | **tracked_set** | **epoch** |
| TrackedRegexDate | **tracked_regex** | **epoch** |
| | | |
| BlackListTermDate | **blacklisted_term** | **epoch** |
| | | |
| **epoch** | **term** | **nb_seen** |

## DB6 - Tags:

##### Hset:
| Key | Field | Value |
| ------ | ------ | ------ |
| per_paste_**epoch** | **term** | **nb_seen** |
| | |
| tag_metadata:**tag** | first_seen | **date** |
| tag_metadata:**tag** | last_seen | **date** |

##### Set:
| Key | Value |
| ------ | ------ |
| list_tags | **tag** |
| active_taxonomies | **taxonomie** |
| active_galaxies | **galaxie** |
| active_tag_**taxonomie or galaxy** | **tag** |
| synonym_tag_misp-galaxy:**galaxy** | **tag synonym** |
| list_export_tags | **user_tag** |
| **tag**:**date** | **paste** |


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

#### Cryptocurrency

Supported cryptocurrency:
- bitcoin

##### Hset:
| Key | Field | Value |
| ------ | ------ | ------ |
| cryptocurrency_metadata_**cryptocurrency name**:**cryptocurrency address** | first_seen | **date** |
| | last_seen | **date** |

##### set:
| Key | Value |
| ------ | ------ |
| set_cryptocurrency_**cryptocurrency name**:**cryptocurrency address** | **item_path** |

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
| item_cryptocurrency_**cryptocurrency name**:**item_path** | **cryptocurrency address** |


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

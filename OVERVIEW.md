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

## Tags:

##### Hset:
| Key | Field | Value |
| ------ | ------ | ------ |
| daily_tags:**date** | **tag** | **nb tagged this day** |
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
| crawler\_history\_**service type**:**domain** | **item root (first crawled item)** | **epoch (seconds)** |

##### Key:
| Key | Value |
| ------ | ------ |
| crawler\_config:**crawler mode**:**service type**:**domain** | **json config** |

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

* DB 2 - TermFreq
	----------------------------------------- TERM ----------------------------------------

	SET - 'TrackedRegexSet'				term

	HSET - 'TrackedRegexDate'			tracked_regex		today_timestamp

	SET - 'TrackedSetSet'				set_to_add

	HSET - 'TrackedSetDate'				set_to_add		today_timestamp

	SET - 'TrackedSetTermSet'			term

	HSET - 'TrackedTermDate'			tracked_regex		today_timestamp

	SET - 'TrackedNotificationEmails_'+term/set	email

	SET - 'TrackedNotifications'			term/set

* DB 4 - Sentiment
	----------------------------------------- SENTIMENT ------------------------------------

	SET - 'Provider_set'				Provider

	KEY - 'UniqID' 					INT

	SET - provider_timestamp			UniqID

	SET - UniqID					avg_score

  DB 5 - TermCred



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

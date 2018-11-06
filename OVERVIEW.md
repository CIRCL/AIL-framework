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
    - DB 1 - Curve
    - DB 2 - Trending
    - DB 3 - Terms
    - DB 4 - Sentiments
* ARDB on TCP port <year>
    - DB 0 - Lines duplicate
    - DB 1 - Hashes


ARDB overview
---------------------------
ARDB_DB
* DB 1 - Curve
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

* DB 3 - Trending
* DB 4 - Sentiment
* DB 5 - TermCred
* DB 6 - Tags
* DB 7 - Metadata
* DB 8 - Statistics

* DB 7 - Metadata:
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

	SET  - 'hash_paste:'+paste	hash *
	SET  - 'base64_paste:'+paste	hash *
	SET  - 'binary_paste:'+paste	hash *

	ZADD - 'hash_date:'+20180622	hash *			nb_seen_this_day
	ZADD - 'base64_date:'+20180622	hash *			nb_seen_this_day
	ZADD - 'binary_date:'+20180622	hash *			nb_seen_this_day

	ZADD - 'nb_seen_hash:'+hash	paste *			nb_seen_in_paste
	ZADD - 'base64_hash:'+hash	paste *			nb_seen_in_paste
	ZADD - 'binary_hash:'+hash	paste *			nb_seen_in_paste

	ZADD - 'hash_type:'+type	date			nb_seen
	ZADD - 'base64_type:'+type	date			nb_seen
	ZADD - 'binary_type:'+type	date			nb_seen

	GET  - 'base64_decoded:'+date	nd_decoded
	GET  - 'binary_decoded:'+date	nd_decoded

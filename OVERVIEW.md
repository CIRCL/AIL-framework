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

	SET  - 'hash_base64_all_type'	hash_type *
	SET  - 'hash_binary_all_type'	hash_type *

	SET  - 'base64_paste:'+paste	hash *
	SET  - 'binary_paste:'+paste	hash *

	ZADD - 'base64_date:'+20180622	hash *			nb_seen_this_day

	ZADD - 'base64_hash'+hash	paste *			nb_seen_in_paste
	ZADD - 'binary_hash'+hash	paste *			nb_seen_in_paste

	SET  - 'hash_all_type'		hash_type

	ZADD - 'base64_type:'+type	date			nb_seen
	ZADD - 'binary_type:'+type	date			nb_seen

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
* DB 3 - Trending
* DB 4 - Sentiment
* DB 5 - TermCred
* DB 6 - Tags
* DB 7 - Metadata
* DB 8 - Statistics

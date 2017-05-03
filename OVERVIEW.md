Overview
========

Redis and LevelDB overview
--------------------------

* Redis on TCP port 6379 - DB 0 - Cache hostname/dns
*                          DB 1 - Paste meta-data
* Redis on TCP port 6380 - Redis Log only
* Redis on TCP port 6381 - DB 0 - PubSub + Queue and Paste content LRU cache
                           DB 1 - __Mixer__ Cache
* LevelDB on TCP port 6382 - DB 1-4 - Curve, Trending, Terms and Sentiments
* LevelDB on TCP port <year> - DB 0 - Lines duplicate
                               DB 1 - Hashs


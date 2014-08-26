#!/usr/bin/env python2
# -*-coding:UTF-8 -*

"""
The Duplicate module
====================

This huge module is, in short term, checking duplicates.

Requirements:
-------------


"""
import redis
import os
import time
from packages import Paste
from pubsublogger import publisher
from pybloomfilter import BloomFilter

import Helper

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'PubSub_Global'
    config_channel = 'channel'
    subscriber_name = 'duplicate'

    h = Helper.Redis_Queues(config_section, config_channel, subscriber_name)

    # REDIS #
    # DB OBJECT & HASHS ( DISK )
    # FIXME increase flexibility
    dico_redis = {}
    for year in xrange(2013, 2015):
        for month in xrange(0, 16):
            dico_redis[str(year)+str(month).zfill(2)] = redis.StrictRedis(
                host=h.config.get("Redis_Level_DB", "host"), port=year,
                db=month)

    # FUNCTIONS #
    publisher.info("""Script duplicate subscribed to channel {0}""".format(
        h.config.get("PubSub_Global", "channel")))

    set_limit = 100
    bloompath = os.path.join(os.environ['AIL_HOME'],
                             h.config.get("Directories", "bloomfilters"))

    bloop_path_set = set()
    while True:
        try:
            super_dico = {}
            hash_dico = {}
            dupl = []
            nb_hash_current = 0

            x = time.time()

            message = h.redis_rpop()
            if message is not None:
                path = message.split(" ", -1)[-1]
                PST = Paste.Paste(path)
            else:
                publisher.debug("Script Attribute is idling 10s")
                time.sleep(10)
                if h.redis_queue_shutdown():
                    print "Shutdown Flag Up: Terminating"
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                continue

            PST._set_p_hash_kind("md5")

            # Assignate the correct redis connexion
            r_serv1 = dico_redis[PST.p_date.year + PST.p_date.month]

            # Creating the bloom filter name: bloomyyyymm
            filebloompath = os.path.join(bloompath, 'bloom' + PST.p_date.year +
                                         PST.p_date.month)

            if os.path.exists(filebloompath):
                bloom = BloomFilter.open(filebloompath)
            else:
                bloom = BloomFilter(100000000, 0.01, filebloompath)
                bloop_path_set.add(filebloompath)

            # UNIQUE INDEX HASHS TABLE
            r_serv0 = dico_redis["201300"]
            r_serv0.incr("current_index")
            index = r_serv0.get("current_index")+str(PST.p_date)
            # HASHTABLES PER MONTH (because of r_serv1 changing db)
            r_serv1.set(index, PST.p_path)
            r_serv1.sadd("INDEX", index)

            # For each bloom filter
            opened_bloom = []
            for bloo in bloop_path_set:
                # Opening blooms
                opened_bloom.append(BloomFilter.open(bloo))

            # For each hash of the paste
            for line_hash in PST._get_hash_lines(min=5, start=1, jump=0):
                nb_hash_current += 1

                # Adding the hash in Redis & limiting the set
                if r_serv1.scard(line_hash) <= set_limit:
                    r_serv1.sadd(line_hash, index)
                    r_serv1.sadd("HASHS", line_hash)
                # Adding the hash in the bloom of the month
                bloom.add(line_hash)

                # Go throught the Database of the bloom filter (of the month)
                for bloo in opened_bloom:
                    if line_hash in bloo:
                        db = bloo.name[-6:]
                        # Go throught the Database of the bloom filter (month)
                        r_serv_bloom = dico_redis[db]

                        # set of index paste: set([1,2,4,65])
                        hash_current = r_serv_bloom.smembers(line_hash)
                        # removing itself from the list
                        hash_current = hash_current - set([index])

                        # if the hash is present at least in 1 files
                        # (already processed)
                        if len(hash_current) != 0:
                            hash_dico[line_hash] = hash_current

                        # if there is data in this dictionnary
                        if len(hash_dico) != 0:
                            super_dico[index] = hash_dico

    ###########################################################################

            # if there is data in this dictionnary
            if len(super_dico) != 0:
                # current = current paste, phash_dico = {hash: set, ...}
                occur_dico = {}
                for current, phash_dico in super_dico.items():
                    # phash = hash, pset = set([ pastes ...])
                    for phash, pset in hash_dico.items():

                        for p_fname in pset:
                            occur_dico.setdefault(p_fname, 0)
                            # Count how much hash is similar per file occuring
                            # in the dictionnary
                            if occur_dico[p_fname] >= 0:
                                occur_dico[p_fname] = occur_dico[p_fname] + 1

                for paste, count in occur_dico.items():
                    percentage = round((count/float(nb_hash_current))*100, 2)
                    if percentage >= 50:
                        dupl.append((paste, percentage))

                # Creating the object attribute and save it.
                to_print = 'Duplicate;{};{};{};'.format(
                    PST.p_source, PST.p_date, PST.p_name)
                if dupl != []:
                    PST.__setattr__("p_duplicate", dupl)
                    PST.save_attribute_redis("p_duplicate", dupl)
                    publisher.info('{}Detected {}'.format(to_print, len(dupl)))

                y = time.time()

                publisher.debug('{}Processed in {} sec'.format(to_print, y-x))
        except IOError:
            print "CRC Checksum Failed on :", PST.p_path
            publisher.error('{}CRC Checksum Failed'.format(to_print))

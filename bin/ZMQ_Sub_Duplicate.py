#!/usr/bin/env python2
# -*-coding:UTF-8 -*

"""
The Duplicate module
====================

This huge module is, in short term, checking duplicates.

Requirements:
-------------


"""
import redis, zmq, ConfigParser, time, datetime, pprint, time, os
from packages import Paste as P
from packages import ZMQ_PubSub
from datetime import date
from pubsublogger import publisher
from pybloomfilter import BloomFilter

configfile = './packages/config.cfg'

def main():
    """Main Function"""

    # CONFIG #
    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)

    # REDIS #
    # DB QUEUE ( MEMORY )
    r_Q_serv = redis.StrictRedis(
        host = cfg.get("Redis_Queues", "host"),
        port = cfg.getint("Redis_Queues", "port"),
        db = cfg.getint("Redis_Queues", "db"))

    r_serv_merge = redis.StrictRedis(
        host = cfg.get("Redis_Data_Merging", "host"),
        port = cfg.getint("Redis_Data_Merging", "port"),
        db = cfg.getint("Redis_Data_Merging", "db"))


    # REDIS #
    # DB OBJECT & HASHS ( DISK )
    dico_redis = {}
    for year in xrange(2013, 2015):
        for month in xrange(0,16):
            dico_redis[str(year)+str(month).zfill(2)] = redis.StrictRedis(
                host = cfg.get("Redis_Level_DB", "host"),
                port = year,
                db = month)

    # LOGGING #
    publisher.channel = "Script"

    # ZMQ #
    channel = cfg.get("PubSub_Global", "channel")
    subscriber_name = "duplicate"
    subscriber_config_section = "PubSub_Global"

    Sub = ZMQ_PubSub.ZMQSub(configfile, subscriber_config_section, channel, subscriber_name)

    # FUNCTIONS #
    publisher.info("""Script duplicate subscribed to channel {0}""".format(cfg.get("PubSub_Global", "channel")))

    set_limit = 100

    while True:
        try:
            super_dico = {}
            hash_dico = {}
            dupl = []
            nb_hash_current = 0

            x = time.time()

            message = Sub.get_msg_from_queue(r_Q_serv)
            if message != None:
                path = message.split(" ",-1)[-1]
                PST = P.Paste(path)
            else:
                publisher.debug("Script Attribute is idling 10s")
                time.sleep(10)
                if r_Q_serv.sismember("SHUTDOWN_FLAGS", "Duplicate"):
                    r_Q_serv.srem("SHUTDOWN_FLAGS", "Duplicate")
                    print "Shutdown Flag Up: Terminating"
                    publisher.warning("Shutdown Flag Up: Terminating.")
                    break
                continue

            PST._set_p_hash_kind("md5")

            #Assignate the correct redis connexion
            r_serv1 = dico_redis[PST.p_date.year + PST.p_date.month]

            #Creating the bloom filter name: bloomyyyymm
            bloomname = 'bloom' + PST.p_date.year + PST.p_date.month

            bloompath = cfg.get("Directories", "bloomfilters")

            filebloompath = bloompath + bloomname

            #datetime.date(int(PST.p_date.year),int(PST.p_date.month),int(PST.p_date.day)).timetuple().tm_yday % 7

            if os.path.exists(filebloompath):
                bloom = BloomFilter.open(filebloompath)
            else:
                bloom = BloomFilter(100000000, 0.01, filebloompath)
                r_Q_serv.sadd("bloomlist", filebloompath)

            # UNIQUE INDEX HASHS TABLE
            r_serv0 = dico_redis["201300"]
            r_serv0.incr("current_index")
            index = r_serv0.get("current_index")+str(PST.p_date)
            # HASHTABLES PER MONTH (because of r_serv1 changing db)
            r_serv1.set(index, PST.p_path)
            r_serv1.sadd("INDEX", index)

            #For each bloom filter
            opened_bloom = []
            for bloo in r_Q_serv.smembers("bloomlist"):
                #Opening blooms
                opened_bloom.append(BloomFilter.open(bloo))

            # For each hash of the paste
            for hash in PST._get_hash_lines(min = 5, start = 1, jump = 0):
                nb_hash_current += 1

                #Adding the hash in Redis & limiting the set
                if r_serv1.scard(hash) <= set_limit:
                    r_serv1.sadd(hash, index)
                    r_serv1.sadd("HASHS", hash)
                #Adding the hash in the bloom of the month
                bloom.add(hash)

                #Go throught the Database of the bloom filter (of the month)
                for bloo in opened_bloom:
                    if hash in bloo:
                        db = bloo.name[-6:]
                        #Go throught the Database of the bloom filter (of the month)
                        r_serv_bloom = dico_redis[db]

                        #set of index paste: set([1,2,4,65])
                        hash_current = r_serv_bloom.smembers(hash)
                        #removing itself from the list
                        hash_current = hash_current - set([index])

                        # if the hash is present at least in 1 files (already processed)
                        if len(hash_current) != 0:
                            hash_dico[hash] = hash_current

                        #if there is data in this dictionnary
                        if len(hash_dico) != 0:
                            super_dico[index] = hash_dico
                    else:
                        # The hash is not in this bloom
                        pass

    ###########################################################################################

            #if there is data in this dictionnary
            if len(super_dico) != 0:
                # current = current paste, phash_dico = {hash: set, ...}
                occur_dico = {}
                for current, phash_dico in super_dico.items():
                    nb_similar_hash = len(phash_dico)
                    # phash = hash, pset = set([ pastes ...])
                    for phash, pset in hash_dico.items():

                        for p_fname in pset:
                            occur_dico.setdefault(p_fname, 0)
                            # Count how much hash is similar per file occuring in the dictionnary
                            if occur_dico[p_fname] >= 0:
                                occur_dico[p_fname] = occur_dico[p_fname] + 1

                for paste, count in occur_dico.items():
                    percentage = round((count/float(nb_hash_current))*100, 2)
                    if percentage >= 50:
                        dupl.append((paste, percentage))

                # Creating the object attribute and save it.
                if dupl != []:
                    PST.__setattr__("p_duplicate", dupl)
                    PST.save_attribute_redis(r_serv_merge, "p_duplicate", dupl)
                    publisher.info('{0};{1};{2};{3};{4}'.format("Duplicate", PST.p_source, PST.p_date, PST.p_name,"Detected " + str(len(dupl))))

                y = time.time()

                publisher.debug('{0};{1};{2};{3};{4}'.format("Duplicate", PST.p_source, PST.p_date, PST.p_name, "Processed in "+str(y-x)+ " sec" ))
        except IOError:
            print "CRC Checksum Failed on :", PST.p_path
            publisher.error('{0};{1};{2};{3};{4}'.format("Duplicate", PST.p_source, PST.p_date, PST.p_name, "CRC Checksum Failed" ))
            pass

if __name__ == "__main__":
    main()

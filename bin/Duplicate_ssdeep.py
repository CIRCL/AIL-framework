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
import datetime
import json
import ssdeep
from packages import Paste
from pubsublogger import publisher

from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Duplicates'
    save_dico_and_reload = 1 #min
    time_1 = time.time()
    flag_reload_from_disk = True
    flag_write_to_disk = False

    p = Process(config_section)

    # REDIS #
    # DB OBJECT & HASHS ( DISK )
    # FIXME increase flexibility
    dico_redis = {}
    for year in xrange(2013, datetime.date.today().year+1):
        for month in xrange(0, 16):
            dico_redis[str(year)+str(month).zfill(2)] = redis.StrictRedis(
                host=p.config.get("Redis_Level_DB", "host"), port=year,
                db=month)
	    #print("dup: "+str(year)+str(month).zfill(2)+"\n")

    # FUNCTIONS #
    publisher.info("Script duplicate started")

    dicopath = os.path.join(os.environ['AIL_HOME'],
                             p.config.get("Directories", "dicofilters"))

    dico_path_set = set()
    while True:
        try:
            hash_dico = {}
            dupl = []

            x = time.time()

            message = p.get_from_set()
            if message is not None:
                path = message
                PST = Paste.Paste(path)
            else:
                publisher.debug("Script Attribute is idling 10s")
                time.sleep(10)
                continue

            PST._set_p_hash_kind("ssdeep")

            # Assignate the correct redis connexion
            r_serv1 = dico_redis[PST.p_date.year + PST.p_date.month]

            # Creating the dicor name: dicoyyyymm
            filedicopath = os.path.join(dicopath, 'dico' + PST.p_date.year +
                                         PST.p_date.month)
            filedicopath_today = filedicopath

            # Save I/O
            if time.time() - time_1 > save_dico_and_reload*60:
                flag_write_to_disk = True

            if os.path.exists(filedicopath):
                if flag_reload_from_disk == True:
                    flag_reload_from_disk = False
                    print 'Reloading'
                    with open(filedicopath, 'r') as fp:
                        today_dico = json.load(fp)
            else:
                today_dico = {}
                with open(filedicopath, 'w') as fp:
                    json.dump(today_dico, fp)

            # For now, just use monthly dico
            dico_path_set.add(filedicopath)

            # UNIQUE INDEX HASHS TABLE
            yearly_index = str(datetime.date.today().year)+'00'
            r_serv0 = dico_redis[yearly_index]
            r_serv0.incr("current_index")
            index = r_serv0.get("current_index")+str(PST.p_date)
            
            # For each dico
            opened_dico = []
            for dico in dico_path_set:
                # Opening dico
                if dico == filedicopath_today:
                    opened_dico.append([dico, today_dico])
                else:
                    with open(dico, 'r') as fp:
                        opened_dico.append([dico, json.load(fp)])

              
            #retrieve hash from paste
            paste_hash = PST._get_p_hash()
            
            # Go throught the Database of the dico (of the month)
            threshold_dup = 99 
            for dico_name, dico in opened_dico:
                for dico_key, dico_hash in dico.items():
                    percent = ssdeep.compare(dico_hash, paste_hash)
                    if percent > threshold_dup:
                        db = dico_name[-6:]
                        # Go throught the Database of the dico filter (month)
                        r_serv_dico = dico_redis[db]
                        
                        # index of paste
                        index_current = r_serv_dico.get(dico_hash)
                        paste_path = r_serv_dico.get(index_current)
                        if paste_path != None:
                            hash_dico[dico_hash] = (paste_path, percent)

                        #print 'comparing: ' + str(dico_hash[:20]) + '  and  ' + str(paste_hash[:20]) + ' percentage: ' + str(percent)
                        print '   '+ PST.p_path[44:]  +', '+ paste_path[44:] + ', ' + str(percent)

            # Add paste in DB to prevent its analyse twice
            # HASHTABLES PER MONTH (because of r_serv1 changing db)
            r_serv1.set(index, PST.p_path)
            r_serv1.sadd("INDEX", index)
            # Adding the hash in Redis
            r_serv1.set(paste_hash, index)
            r_serv1.sadd("HASHS", paste_hash)
    ##################### Similarity found  #######################

            # if there is data in this dictionnary
            if len(hash_dico) != 0:
                for dico_hash, paste_tuple in hash_dico.items():
                    paste_path, percent = paste_tuple
                    dupl.append((paste_path, percent))

                # Creating the object attribute and save it.
                to_print = 'Duplicate;{};{};{};'.format(
                    PST.p_source, PST.p_date, PST.p_name)
                if dupl != []:
                    PST.__setattr__("p_duplicate", dupl)
                    PST.save_attribute_redis("p_duplicate", dupl)
                    publisher.info('{}Detected {}'.format(to_print, len(dupl)))
                    print '{}Detected {}'.format(to_print, len(dupl))

                y = time.time()

                publisher.debug('{}Processed in {} sec'.format(to_print, y-x))
           

            # Adding the hash in the dico of the month
            today_dico[index] = paste_hash

            if flag_write_to_disk:
                time_1 = time.time()
                flag_write_to_disk = False
                flag_reload_from_disk = True
                print 'writing'
                with open(filedicopath, 'w') as fp:
                    json.dump(today_dico, fp)
        except IOError:
            to_print = 'Duplicate;{};{};{};'.format(
                PST.p_source, PST.p_date, PST.p_name)
            print "CRC Checksum Failed on :", PST.p_path
            publisher.error('{}CRC Checksum Failed'.format(to_print))

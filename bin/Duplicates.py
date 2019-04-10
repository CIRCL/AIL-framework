#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The Duplicate module
====================

This huge module is, in short term, checking duplicates.
Its input comes from other modules, namely:
    Credential, CreditCard, Keys, Mails, SQLinjectionDetection, CVE and Phone

This one differ from v1 by only using redis and not json file stored on disk

Perform comparisions with ssdeep and tlsh

Requirements:
-------------


"""
import redis
import os
import time
from datetime import datetime, timedelta
import json
import ssdeep
import tlsh
from packages import Paste
from pubsublogger import publisher

from Helper import Process

if __name__ == "__main__":
    publisher.port = 6380
    publisher.channel = "Script"

    config_section = 'Duplicates'

    p = Process(config_section)

    maximum_month_range = int(p.config.get("Modules_Duplicates", "maximum_month_range"))
    threshold_duplicate_ssdeep = int(p.config.get("Modules_Duplicates", "threshold_duplicate_ssdeep"))
    threshold_duplicate_tlsh = int(p.config.get("Modules_Duplicates", "threshold_duplicate_tlsh"))
    threshold_set = {}
    threshold_set['ssdeep'] = threshold_duplicate_ssdeep
    threshold_set['tlsh'] = threshold_duplicate_tlsh
    min_paste_size = float(p.config.get("Modules_Duplicates", "min_paste_size"))

    # REDIS #
    dico_redis = {}
    date_today = datetime.today()
    for year in range(2013, date_today.year+1):
        for month in range(0, 13):
            dico_redis[str(year)+str(month).zfill(2)] = redis.StrictRedis(
                host=p.config.get("ARDB_DB", "host"),
                port=p.config.get("ARDB_DB", "port"),
                db=str(year) + str(month),
                decode_responses=True)

    # FUNCTIONS #
    publisher.info("Script duplicate started")

    while True:
        try:
            hash_dico = {}
            dupl = set()
            dico_range_list = []

            x = time.time()

            message = p.get_from_set()
            if message is not None:
                path = message
                PST = Paste.Paste(path)
            else:
                publisher.debug("Script Attribute is idling 10s")
                print('sleeping')
                time.sleep(10)
                continue

            # the paste is too small
            if (PST._get_p_size() < min_paste_size):
                continue

            PST._set_p_hash_kind("ssdeep")
            PST._set_p_hash_kind("tlsh")

            # Assignate the correct redis connexion
            r_serv1 = dico_redis[PST.p_date.year + PST.p_date.month]

            # Creating the dico name: yyyymm
            # Get the date of the range
            date_range = date_today - timedelta(days = maximum_month_range*30.4166666)
            num_of_month = (date_today.year - date_range.year)*12 + (date_today.month - date_range.month)
            for diff_month in range(0, num_of_month+1):
                curr_date_range = date_today - timedelta(days = diff_month*30.4166666)
                to_append = str(curr_date_range.year)+str(curr_date_range.month).zfill(2)
                dico_range_list.append(to_append)

            # Use all dico in range
            dico_range_list = dico_range_list[0:maximum_month_range]

            # UNIQUE INDEX HASHS TABLE
            yearly_index = str(date_today.year)+'00'
            r_serv0 = dico_redis[yearly_index]
            r_serv0.incr("current_index")
            index = (r_serv0.get("current_index")) + str(PST.p_date)

            # Open selected dico range
            opened_dico = []
            for dico_name in dico_range_list:
                opened_dico.append([dico_name, dico_redis[dico_name]])

            # retrieve hash from paste
            paste_hashes = PST._get_p_hash()

            # Go throught the Database of the dico (of the month)
            for curr_dico_name, curr_dico_redis in opened_dico:
                for hash_type, paste_hash in paste_hashes.items():
                    for dico_hash in curr_dico_redis.smembers('HASHS_'+hash_type):

                        try:
                            if hash_type == 'ssdeep':
                                percent = 100-ssdeep.compare(dico_hash, paste_hash)
                            else:
                                percent = tlsh.diffxlen(dico_hash, paste_hash)
                                if percent > 100:
                                    percent = 100

                            threshold_duplicate = threshold_set[hash_type]
                            if percent < threshold_duplicate:
                                percent = 100 - percent if hash_type == 'ssdeep' else percent #recovert the correct percent value for ssdeep
                                # Go throught the Database of the dico filter (month)
                                r_serv_dico = dico_redis[curr_dico_name]

                                # index of paste
                                index_current = r_serv_dico.get(dico_hash)
                                index_current = index_current
                                paste_path = r_serv_dico.get(index_current)
                                paste_path = paste_path
                                paste_date = r_serv_dico.get(index_current+'_date')
                                paste_date = paste_date
                                paste_date = paste_date if paste_date != None else "No date available"
                                if paste_path != None:
                                    if paste_path != PST.p_rel_path:
                                        hash_dico[dico_hash] = (hash_type, paste_path, percent, paste_date)

                                        print('['+hash_type+'] '+'comparing: ' + str(PST.p_rel_path) + '  and  ' + str(paste_path) + ' percentage: ' + str(percent))

                        except Exception:
                            print('hash not comparable, bad hash: '+dico_hash+' , current_hash: '+paste_hash)

            # Add paste in DB after checking to prevent its analysis twice
            # hash_type_i -> index_i  AND  index_i -> PST.PATH
            r_serv1.set(index, PST.p_rel_path)
            r_serv1.set(index+'_date', PST._get_p_date())
            r_serv1.sadd("INDEX", index)
            # Adding hashes in Redis
            for hash_type, paste_hash in paste_hashes.items():
                r_serv1.set(paste_hash, index)
                #bad hash
                if paste_hash == '':
                    print('bad Hash: ' + hash_type)
                else:
                    r_serv1.sadd("HASHS_"+hash_type, paste_hash)

    ##################### Similarity found  #######################

            # if there is data in this dictionnary
            if len(hash_dico) != 0:
                # paste_tuple = (hash_type, date, paste_path, percent)
                for dico_hash, paste_tuple in hash_dico.items():
                    dupl.add(paste_tuple)

                # Creating the object attribute and save it.
                to_print = 'Duplicate;{};{};{};'.format(
                    PST.p_source, PST.p_date, PST.p_name)
                if dupl != []:
                    dupl = list(dupl)
                    PST.__setattr__("p_duplicate", dupl)
                    PST.save_attribute_duplicate(dupl)
                    PST.save_others_pastes_attribute_duplicate(dupl)
                    publisher.info('{}Detected {};{}'.format(to_print, len(dupl), PST.p_rel_path))
                    print('{}Detected {}'.format(to_print, len(dupl)))
                    print('')

                y = time.time()

                publisher.debug('{}Processed in {} sec'.format(to_print, y-x))

        except IOError:
            to_print = 'Duplicate;{};{};{};'.format(
                PST.p_source, PST.p_date, PST.p_name)
            print("CRC Checksum Failed on :", PST.p_rel_path)
            publisher.error('{}CRC Checksum Failed'.format(to_print))

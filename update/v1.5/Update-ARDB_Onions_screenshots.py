#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time
import redis
import datetime

from hashlib import sha256

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib/'))
import ConfigLoader

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def substract_date(date_from, date_to):
    date_from = datetime.date(int(date_from[0:4]), int(date_from[4:6]), int(date_from[6:8]))
    date_to = datetime.date(int(date_to[0:4]), int(date_to[4:6]), int(date_to[6:8]))
    delta = date_to - date_from # timedelta
    l_date = []
    for i in range(delta.days + 1):
        date = date_from + datetime.timedelta(i)
        l_date.append( date.strftime('%Y%m%d') )
    return l_date

if __name__ == '__main__':

    start_deb = time.time()

    config_loader = ConfigLoader.ConfigLoader()

    SCREENSHOT_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "crawled_screenshot"))
    NEW_SCREENSHOT_FOLDER = config_loader.get_files_directory('screenshot')

    PASTES_FOLDER = os.path.join(os.environ['AIL_HOME'], config_loader.get_config_str("Directories", "pastes")) + '/'

    r_serv = config_loader.get_redis_conn("ARDB_DB")
    r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")
    r_serv_tag = config_loader.get_redis_conn("ARDB_Tags")
    r_serv_onion = config_loader.get_redis_conn("ARDB_Onion")
    config_loader = None

    r_serv.set('ail:current_background_script', 'crawled_screenshot')
    r_serv.set('ail:current_background_script_stat', 0)

    ## Update Onion ##
    print('Updating ARDB_Onion ...')
    index = 0
    start = time.time()

    # clean down domain from db
    date_from = '20180801'
    date_today = datetime.date.today().strftime("%Y%m%d")
    list_date = substract_date(date_from, date_today)
    nb_done = 0
    last_progress = 0
    total_to_update = len(list_date)
    for date in list_date:
        screenshot_dir = os.path.join(SCREENSHOT_FOLDER, date[0:4], date[4:6], date[6:8])
        if os.path.isdir(screenshot_dir):
            print(screenshot_dir)
            for file in os.listdir(screenshot_dir):
                if file.endswith(".png"):
                    index += 1
                    #print(file)

                    img_path = os.path.join(screenshot_dir, file)
                    with open(img_path, 'br') as f:
                        image_content = f.read()

                    hash = sha256(image_content).hexdigest()
                    img_dir_path = os.path.join(hash[0:2], hash[2:4], hash[4:6], hash[6:8], hash[8:10], hash[10:12])
                    filename_img = os.path.join(NEW_SCREENSHOT_FOLDER, img_dir_path, hash[12:] +'.png')
                    dirname = os.path.dirname(filename_img)
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)
                    if not os.path.exists(filename_img):
                        os.rename(img_path, filename_img)
                    else:
                        os.remove(img_path)

                    item = os.path.join('crawled', date[0:4], date[4:6], date[6:8], file[:-4])
                    # add item metadata
                    r_serv_metadata.hset('paste_metadata:{}'.format(item), 'screenshot', hash)
                    # add sha256 metadata
                    r_serv_onion.sadd('screenshot:{}'.format(hash), item)

                if file.endswith('.pnghar.txt'):
                    har_path = os.path.join(screenshot_dir, file)
                    new_file = rreplace(file, '.pnghar.txt', '.json', 1)
                    new_har_path = os.path.join(screenshot_dir, new_file)
                    os.rename(har_path, new_har_path)

        progress = int((nb_done * 100) /total_to_update)
        # update progress stats
        if progress != last_progress:
            r_serv.set('ail:current_background_script_stat', progress)
            print('{}/{}    screenshot updated    {}%'.format(nb_done, total_to_update, progress))
            last_progress = progress

        nb_done += 1

    r_serv.set('ail:current_background_script_stat', 100)


    end = time.time()
    print('Updating ARDB_Onion Done => {} paths: {} s'.format(index, end - start))
    print()
    print('Done in {} s'.format(end - start_deb))

    r_serv.set('ail:current_background_script_stat', 100)
    r_serv.sadd('ail:update_v1.5', 'crawled_screenshot')
    if r_serv.scard('ail:update_v1.5') != 5:
        r_serv.set('ail:update_error', 'Update v1.5 Failed, please relaunch the bin/update-background.py script')

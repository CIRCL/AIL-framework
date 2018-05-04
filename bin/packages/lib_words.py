#!/usr/bin/python3

import os
import string

from pubsublogger import publisher

import calendar
from datetime import date
from dateutil.rrule import rrule, DAILY
import csv


def listdirectory(path):
    """Path Traversing Function.

    :param path: -- The absolute pathname to a directory.

    This function is returning all the absolute path of the files contained in
    the argument directory.

    """
    fichier = []
    for root, dirs, files in os.walk(path):

        for i in files:

            fichier.append(os.path.join(root, i))

    return fichier

clean = lambda dirty: ''.join(filter(string.printable.__contains__, dirty))
"""It filters out non-printable characters from the string it receives."""


def create_dirfile(r_serv, directory, overwrite):
    """Create a file of path.

    :param r_serv: -- connexion to redis database
    :param directory: -- The folder where to launch the listing of the .gz files

    This function create a list in redis with inside the absolute path
    of all the pastes needed to be proceeded by function using parallel
    (like redis_words_ranking)

    """
    if overwrite:
        r_serv.delete("filelist")

        for x in listdirectory(directory):
            r_serv.lpush("filelist", x)

        publisher.info("The list was overwritten")

    else:
        if r_serv.llen("filelist") == 0:

            for x in listdirectory(directory):
                r_serv.lpush("filelist", x)

            publisher.info("New list created")
        else:

            for x in listdirectory(directory):
                r_serv.lpush("filelist", x)

            publisher.info("The list was updated with new elements")


def create_curve_with_word_file(r_serv, csvfilename, feederfilename, year, month):
    """Create a csv file used with dygraph.

    :param r_serv: -- connexion to redis database
    :param csvfilename: -- the path to the .csv file created
    :param feederfilename: -- the path to the file which contain a list of words.
    :param year: -- (integer) The year to process
    :param month: -- (integer) The month to process

    This function create a .csv file using datas in redis.
    It's checking if the words contained in feederfilename and
    their respectives values by days exists. If these values are missing
    (Word not present during a day) it's will automatically put a 0
    to keep the timeline of the curve correct.

    """
    threshold = 30
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    words = []

    with open(feederfilename, 'r') as f:
        # words of the files
        words = sorted([word.strip() for word in f if word.strip()[0:2]!='//' and word.strip()!='' ])

    headers = ['Date'] + words
    with open(csvfilename+'.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        # for each days
        for dt in rrule(DAILY, dtstart=first_day, until=last_day):
            row = []
            curdate = dt.strftime("%Y%m%d")
            row.append(curdate)
            # from the 1srt day to the last of the list
            for word in words:
                value = r_serv.hget(word, curdate)

                if value is None:
                    row.append(0)
                else:
                    # if the word have a value for the day
                    # FIXME Due to performance issues (too many tlds, leads to more than 7s to perform this procedure), I added a threshold
                    value = r_serv.hget(word, curdate)
                    value = int(value)
                    if value >= threshold:
                        row.append(value)
            writer.writerow(row)

def create_curve_from_redis_set(server, csvfilename, set_to_plot, year, month):
    """Create a csv file used with dygraph.

    :param r_serv: -- connexion to redis database
    :param csvfilename: -- the path to the .csv file created
    :param to_plot: -- the list which contain a words to plot.
    :param year: -- (integer) The year to process
    :param month: -- (integer) The month to process

    This function create a .csv file using datas in redis.
    It's checking if the words contained in set_to_plot and
    their respectives values by days exists.

    """

    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    redis_set_name = set_to_plot + "_set_" + str(year) + str(month).zfill(2)
    words = list(server.smembers(redis_set_name))
    #words = [x.decode('utf-8') for x in words]

    headers = ['Date'] + words
    with open(csvfilename+'.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        # for each days
        for dt in rrule(DAILY, dtstart=first_day, until=last_day):
            row = []
            curdate = dt.strftime("%Y%m%d")
            row.append(curdate)
            # from the 1srt day to the last of the list
            for word in words:
                value = server.hget(word, curdate)
                if value is None:
                    row.append(0)
                else:
                    # if the word have a value for the day
                    row.append(value)
            writer.writerow(row)

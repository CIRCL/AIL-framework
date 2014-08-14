import redis, gzip

import numpy as np
import matplotlib.pyplot as plt
from pylab import *

from textblob import TextBlob
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer

from lib_redis_insert import clean, listdirectory
from lib_jobs import *

from pubsublogger import publisher

import calendar as cal
from datetime import date, timedelta
from dateutil.rrule import rrule, DAILY

from packages import *


def listdirectory(path):
    """Path Traversing Function.

    :param path: -- The absolute pathname to a directory.

    This function is returning all the absolute path of the files contained in
    the argument directory.

    """
    fichier=[]
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
            r_serv.rpush("filelist",x)

        publisher.info("The list was overwritten")

    else:
        if r_serv.llen("filelist") == 0:

            for x in listdirectory(directory):
                r_serv.rpush("filelist",x)

            publisher.info("New list created")
        else:

            for x in listdirectory(directory):
                r_serv.rpush("filelist",x)

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
    a = date(year, month, 01)
    b = date(year, month, cal.monthrange(year,month)[1])
    days = {}
    words = []

    with open(feederfilename, 'rb') as F:
        for word in F: # words of the files
            words.append(word[:-1]) # list of words (sorted as in the file)

        for dt in rrule(DAILY, dtstart = a, until = b): # for each days

            mot = []
            mot1 = []
            mot2 = []

            days[dt.strftime("%Y%m%d")] = ''
            for word in sorted(words): # from the 1srt day to the last of the list
                if r_serv.hexists(word, dt.strftime("%Y%m%d")): # if the word have a value for the day
                    mot1.append(str(word))
                    mot2.append(r_serv.hget(word, dt.strftime("%Y%m%d")))

                    mot = zip(mot1, mot2)

                    days[dt.strftime("%Y%m%d")] = mot
                else:

                    mot1.append(str(word))
                    mot2.append(0)

                    mot = zip(mot1, mot2)

                    days[dt.strftime("%Y%m%d")] = mot

    with open(csvfilename+".csv", 'wb') as F:
        F.write("Date," + ",".join(sorted(words)) + '\n')

        for x, s in days.items():
            val = []
            for y in s:
                val.append(y[1])

            F.write(x + ',' + str(val) + '\n')

    with open(csvfilename+".csv", 'rb') as F:
        h = F.read()
        h = h.replace("[","")
        h = h.replace("]","")
        h = h.replace('\'',"")

    with open(csvfilename+".csv", 'wb') as F:
        F.write(h)

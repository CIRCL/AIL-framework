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

def redis_words_ranking(pipe, r_serv, nb, minlength, maxlength):
    """Looping function

    :param pipe: -- Redis pipe.
    :param nb: -- (int) Number of pastes proceeded by function
    :param minlength: -- (int) passed to the next function
    :param maxlength: -- (int) passed to the next function

    """
    try:
        for n in xrange(0,nb):

                path = r_serv.lpop("filelist")

                if path != None:
                    set_listof_pid(r_serv, path, sys.argv[0])

                    redis_zincr_words(pipe, path, minlength, maxlength)

                    update_listof_pid(r_serv)

                    r_serv.lpush("processed",path)

                    publisher.debug(path)
                else:
                    publisher.debug("Empty list")
                    break
    except (KeyboardInterrupt, SystemExit) as e:
        flush_list_of_pid(r_serv)
        publisher.debug("Pid list flushed")





def redis_zincr_words(pipe, filename, minlength, maxlength):
    """Create news sorted set in redis.

    :param minlength: -- (int) Minimum words length inserted
    :param maxlength: -- (int) Maximum words length inserted
    :param filename: -- The absolute path to the file.gz to process.

    Representation of the set in redis:

    +------------+------------+-----------+
    |     Keys   | Members    | Scores    |
    +============+============+===========+
    | 20131001   | word1      | 142       |
    +------------+------------+-----------+
    | ...        | word2      | 120       |
    +------------+------------+-----------+
    | 20131002   | ...        | ...       |
    +------------+------------+-----------+

    This function store all words between minlength and maxlength in redis.
    Redis will count as well how much time each word will appear by day:
    The cardinality.

    """
    tokenizer = RegexpTokenizer('[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\/\-/\=\'\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]+', gaps = True, discard_empty = True)

    with gzip.open(filename, 'rb') as F:

        blob = TextBlob(clean(F.read()), tokenizer = tokenizer)

        for word in blob.tokens:

            if (len(word) >= minlength) and (len(word) <= maxlength):
                pipe.zincrby(filename[-22:-12].replace('/',''), word, 1)

            if (len(word) >= maxlength):
                publisher.info("word bigger than {0} detected at {1}".format(maxlength, filename))
                publisher.info(word)

        pipe.execute()




def classify_token_paste(r_serv, listname, choicedatastruct, nb, r_set):
    """Tokenizing on word category

    :param r_serv: -- Redis database connexion
    :param listname: -- (str) path to the file containing the list of path of category files
    :param choicedatastruct: -- (bool) Changing the index of datastructure
    :param nb: -- (int) Number of pastes proceeded by function

    Redis data structures cas be choose as follow:

    +---------------+------------+-----------+
    |     Keys      | Members    | Scores    |
    +===============+============+===========+
    | mails_categ   | filename   | 25000     |
    +---------------+------------+-----------+
    | ...           | filename2  | 2400      |
    +---------------+------------+-----------+
    | web_categ     | ...        | ...       |
    +---------------+------------+-----------+

    Or

    +--------------+-------------+-----------+
    |     Keys     | Members     | Scores    |
    +==============+=============+===========+
    | filename     | mails_categ | 100000    |
    +--------------+-------------+-----------+
    | ...          | web_categ   | 24050     |
    +--------------+-------------+-----------+
    | filename2    | ...         | ...       |
    +--------------+-------------+-----------+

    This function tokenise on all special characters like: @^\|[{#~}]!:;$^=
    And insert data in redis if the token match the keywords in a list previously
    created.
    These lists of keywords can be list of everything you want but it's better
    to create "category" of keywords.

    """

    try:
        for n in xrange(0,nb):
            filename = r_serv.lpop(r_set)

            if filename != None:

                tokenizer = RegexpTokenizer('[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\/\-/\=\'\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]+', gaps = True, discard_empty = True)
                set_listof_pid(r_serv, filename, sys.argv[0])

                with open(listname, 'rb') as L:
                    # for each "categ" listed in the file
                    for num, fname in enumerate(L):
                        # contain keywords by categ
                        tmp_list = []
                        #for each keywords
                        with open(fname[:-1], 'rb') as LS:

                            for num, kword in enumerate(LS):
                                tmp_list.append(kword[:-1])

                            # for each paste
                            with gzip.open(filename, 'rb') as F:

                                blob = TextBlob(clean(F.read()),
                                tokenizer = tokenizer)

                                # for each paste token
                                for word in blob.tokens.lower():

                                    if word in tmp_list:
                                        # choosing between two data structures.
                                        if choicedatastruct:
                                            r_serv.zincrby(filename,
                                                fname.split('/')[-1][:-1],
                                                1)
                                        else:
                                            r_serv.zincrby(fname.split('/')[-1][:-1],
                                            filename,
                                            1)

                update_listof_pid(r_serv)

            else:
                publisher.debug("Empty list")
                #r_serv.save()
                break

    except (KeyboardInterrupt, SystemExit) as e:
        flush_list_of_pid(r_serv)
        publisher.debug("Pid list flushed")




def dectect_longlines(r_serv, r_key, store = False, maxlength = 500):
    """Store longlines's linenumbers in redis

    :param r_serv: -- The redis connexion database
    :param r_key: -- (str) The key name in redis
    :param store: -- (bool) Store the line numbers or not.
    :param maxlength: -- The limit between "short lines" and "long lines"

    This function connect to a redis list of filename (pastes filename);
    Open the paste and check inside if there is some line with their
    length >= to maxlength.
    If yes, the paste is "tagged" as containing a longlines in another
    redis structures, and the linenumber (of the long lines) can be stored
    in addition if the argument store is at True.

    """
    try:
        while True:
            #r_key_list (categ)
            filename = r_serv.lpop(r_key)

            if filename != None:

                set_listof_pid(r_serv, filename, sys.argv[0])

                # for each pastes
                with gzip.open(filename, 'rb') as F:
                    var = True
                    for num, line in enumerate(F):

                        if  len(line) >= maxlength:
                            #publisher.debug("Longline:{0}".format(line))
                            if var:
                                r_serv.rpush("longlines", filename)
                                var = False

                            if store:
                                r_serv.sadd(filename, num)
                            else:
                                publisher.debug("Line numbers of longlines not stored")

                update_listof_pid(r_serv)
            else:
                publisher.debug("Empty list")
                return False
                break

    except (KeyboardInterrupt, SystemExit) as e:
        flush_list_of_pid(r_serv)
        publisher.debug("Pid list flushed")




# NOT USED RIGHT NOW #
def recovering_longlines(r_serv):
    """Get longlines with linenumbers

    """
    try:
        for n in xrange(0,nb):
            filename = r_serv.lpop("longlines")

            if filename != None:
                # For each values in redis (longline's line number)
                for numline in r_serv.smembers(filename):

                    with gzip.open(filename,'rb') as F:

                        for num, line in enumerate(F):
                            #When corresponding.
                            if int(num) == int(numline):
                                pass
                                # TREATMENT
            else:
                publisher.debug("Empty list")
                r_serv.save()
                break

    except (KeyboardInterrupt, SystemExit) as e:
        flush_list_of_pid(r_serv)
        publisher.debug("Pid list flushed")




def remove_longline_from_categ(r_serv, r_key, delete, store, maxlength):
    """Remove from a set, file with long lines.

    :param r_serv: -- The redis connexion database
    :param r_key: -- (str) The key name in redis
    :param store: -- (bool) Store the line numbers or not.
    :param delete: -- (bool) If true, delete the used key from redis.
    :param maxlength: -- The limit between "short lines" and "long lines"

    """
    publisher.info("Number of file before:{0}".format(r_serv.zcard(r_key)))

    #Create a list of file to proceed (1)
    for filename in r_serv.zrange(r_key, 0, -1):
        r_serv.rpush(r_key+"_list", filename)

    #detecting longlines in pastes
    dectect_longlines(r_serv, r_key+"_list", store, maxlength)

    #remove false positive members
    while True:
        fp_filename = r_serv.lpop("longlines")

        if fp_filename == None:
            break

        else:
            # if wanted, delete in addition the set with linenumbers (created with store)
            if delete:
                r_serv.zrem(r_key, fp_filename)
                r_serv.delete(fp_filename)

            else:
                #remove the file with longline from the r_key zset.
                r_serv.zrem(r_key, fp_filename)

    publisher.info("Longline file removed from {0}, {1} Files remaining".format(r_key, r_serv.zcard(r_key)))




def detect_longline_from_list(r_serv, nb):
    try:
        for n in xrange(0,nb):

                if not dectect_longlines(r_serv, "filelist", True):
                    break

    except (KeyboardInterrupt, SystemExit) as e:
        flush_list_of_pid(r_serv)
        publisher.debug("Pid list flushed")




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




def redis_interbargraph_set(r_serv, year, month, overwrite):
    """Create a Redis sorted set.

    :param r_serv: -- connexion to redis database
    :param year: -- (integer) The year to process
    :param month: -- (integer) The month to process
    :param overwrite: -- (bool) trigger the overwrite mode

    This function create inside redis the intersection of all days in
    a month two by two.
    Example:
    For a month of 31days it will create 30 sorted set between day and
    day+1 until the last day.
    The overwrite mode delete the intersets and re-create them.

    """
    a = date(year, month, 01)
    b = date(year, month, cal.monthrange(year, month)[1])

    if overwrite:
        r_serv.delete("InterSet")

        for dt in rrule(DAILY, dtstart = a, until = b - timedelta(1)):
            dayafter = dt+timedelta(1)

            r_serv.delete(str(dt.strftime("%Y%m%d"))+str(dayafter.strftime("%Y%m%d")))

            r_serv.zinterstore(
                str(dt.strftime("%Y%m%d"))+str(dayafter.strftime("%Y%m%d")),
                {str(dt.strftime("%Y%m%d")):1,
                str(dayafter.strftime("%Y%m%d")):-1})

            r_serv.zadd(
                "InterSet",
                1,
                str(dt.strftime("%Y%m%d"))+str(dayafter.strftime("%Y%m%d")))
    else:
        for dt in rrule(DAILY, dtstart = a, until = b - timedelta(1)):
            dayafter = dt+timedelta(1)

            if r_serv.zcard(str(dt.strftime("%Y%m%d"))+str(dayafter.strftime("%Y%m%d"))) == 0:

                r_serv.zinterstore(
                    str(dt.strftime("%Y%m%d"))+str(dayafter.strftime("%Y%m%d")),
                    {str(dt.strftime("%Y%m%d")):1,
                    str(dayafter.strftime("%Y%m%d")):-1})

                r_serv.zadd(
                    "InterSet",
                    1,
                    str(dt.strftime("%Y%m%d"))+str(dayafter.strftime("%Y%m%d")))

                publisher.info(str(dt.strftime("%Y%m%d"))+str(dayafter.strftime("%Y%m%d"))+" Intersection Created")

            else:
                publisher.warning("Data already exist, operation aborted.")





def word_bar_graph(r_serv, year, month, filename):
    """Create an histogram.

    :param r_serv: -- connexion to redis database
    :param year: -- (integer) The year to process
    :param month: -- (integer) The month to process
    :param filename: -- The absolute path where to save the figure.png

    This function use matplotlib to create an histogram.
    The redis database need obviously to be populated first
    with functions: redis_words_ranking and redis_interbargraph_set.

    """
    lw = []
    adate = []
    inter = [0]
    rcParams['figure.figsize'] = 15, 10

    a = date(year, month, 01)
    b = date(year, month, cal.monthrange(year,month)[1])

    for dt in rrule(DAILY, dtstart = a, until = b):
        lw.append(r_serv.zcard(dt.strftime("%Y%m%d")))
        adate.append(dt.strftime("%d"))

    for x in r_serv.zrange("InterSet", 0, 31):
        inter.append(r_serv.zcard(x))

    n_groups = len(lw)
    card_words = tuple(lw)
    card_interword = tuple(inter)

    index = np.arange(n_groups)
    bar_width = 0.5
    opacity = 0.6

    words = plt.bar(index, card_words, bar_width,
                 alpha=opacity,
                 color='g',
                 label='Words/day')

    lwords = plt.bar(index - 0.5, card_interword, bar_width,
                 alpha=opacity,
                 color='r',
                 label='Intersection')


    plt.plot(tuple(inter), 'b--')
    plt.xlabel(str(year)+'/'+str(month)+' Days')
    plt.ylabel('Words')
    plt.title('Words Cardinality & Intersection Histogram')
    plt.xticks(index + bar_width/2 , tuple(adate))

    plt.legend()
    plt.grid()

    plt.tight_layout()

    plt.savefig(filename+".png", dpi=None, facecolor='w', edgecolor='b',
        orientation='portrait', papertype=None, format="png",
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=True)

    publisher.info(filename+".png"+" saved!")




def create_data_words_curve(r_serv, r_serv2, year, month, filename):
    """Create a Redis hashes.

    :param r_serv: -- connexion to redis database (read)
    :param r_serv2: -- connexion to redis database (write)
    :param year: -- (integer) The year to process
    :param month: -- (integer) The month to process
    :param filename: -- the path to the file which contain a list of words.


    The hashes of redis is created as follow:

    +------------+------------+-----------+
    |   Keys     | Field      | Values    |
    +============+============+===========+
    | word1      | 20131001   | 150       |
    +------------+------------+-----------+
    | ...        | 20131002   | 145       |
    +------------+------------+-----------+
    | word2      | ...        | ...       |
    +------------+------------+-----------+

    The filename need to be a list of words separated by a carriage return
    with an empty line at the end.
    This function create datas which is used by the function
    create_curve_with_word_file which create a csv file.

    """
    stop = stopwords.words('english')
    a = date(year, month, 01)
    b = date(year, month, cal.monthrange(year,month)[1])

    with open(filename, 'rb') as F:

        for line in F:

            for dt in rrule(DAILY, dtstart = a, until = b):

                if r_serv.zscore(dt.strftime("%Y%m%d"), line[:-1]) is not None:
                    #tester si ca existe deja "en option" et ajouter un WARNING log
                    r_serv2.hmset(line[:-1], {str(dt.strftime("%Y%m%d")):r_serv.zscore(dt.strftime("%Y%m%d"), line[:-1])})
                else:
                    pass




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

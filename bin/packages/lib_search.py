import redis
import string


def create_common_hash_file(r_serv, zmin, zmax, filename):
    """ Create a "top100".txt file.

    :param r_serv: -- connexion to redis database
    :param zmin: -- (int) Offset of the top list
    :param zmax: -- (int) Number of element wanted to be in the top list.
    :param filename: -- the pathname to the created file.

    This Function create a ranking list between zmin and zman of the most common
    hashs.
    Line are written as follow in the file:
    hash:[md5hash]:[cardinality]:[line]
    All hashes represent a full line which mean it can be one char or more...

    """
    with open(filename, 'wb') as F:

        for h, num in r_serv.zrevrangebyscore("hash", "+inf", "-inf", zmin, zmax, True):

            F.write("hash:{0}:{1}:{2}\n".format(h, num, list(r_serv.smembers('L:'+h))))




def paste_searching(r_serv, filename, pastename, mincard, maxcard):
    """Search similar hashs from a given file.

    :param r_serv: -- connexion to redis database
    :param filename: -- the pathname to the created file.
    :param pastename: -- the name of the paste used to search in redis database.
    :param mincard: -- the minimum occurence needed of an hash to be taken in count.
    :param maxcard: -- the maximum occurence needed of an hash to be taken in count.

    This function return a text file which is a kind of synthesis about
    where (in the others pastes) the hash of the given pastename have been found.

    """
    P = set([pastename])
    tmp_h = str()
    tmp_set = set([])

    with open(filename, 'wb') as F:

        F.write("Paste: {0}\nOptions used:\nMincard: {1}\nMaxcard: {2}\n\nContaining Following Hash:\n".format(pastename,mincard,maxcard))

        for h in r_serv.smembers("hash"):

            if (r_serv.smembers(h).intersection(P) and r_serv.scard(h) >= mincard and r_serv.scard(h) <= maxcard):

                F.write(h+'\n')
                tmp_set = tmp_set.union(r_serv.smembers(h).union(r_serv.smembers(tmp_h)))

            tmp_h = h

        F.write("\nSimilar Files:\n")

        for n, s in enumerate(tmp_set):

            F.write(str(n) + ': ' + s + '\n')




def paste_searching2(r_serv, filename, pastename, mincard, maxcard):
    """Search similar hashs from a given file.
    (On another kind of redis data structure)

    :param r_serv: -- connexion to redis database
    :param filename: -- the pathname to the created file.
    :param pastename: -- the name of the paste used to search in redis database.
    :param mincard: -- the minimum occurence needed of an hash to be taken in count.
    :param maxcard: -- the maximum occurence needed of an hash to be taken in count.

    This function return a text file which is a kind of synthesis about
    where (in the others pastes) the hash of the given pastename have been found.

    """
    P = set([pastename])
    tmp_h = str()
    tmp_set = set([])

    with open(filename, 'wb') as F:

        F.write("Paste: {0}\nOptions used:\nMincard: {1}\nMaxcard: {2}\n\n###Containing Following Hash:### ###Occur### ###### Corresponding Line ######\n".format(pastename,mincard,maxcard))

        for h in r_serv.zrange("hash", 0, -1):

            if (r_serv.smembers(h).intersection(P) and r_serv.scard(h) >= mincard and r_serv.scard(h) <= maxcard):

                F.write(h + ' -- ' + str(r_serv.zscore("hash",h)) + ' -- ' + str(list(r_serv.smembers('L:' + h))) + '\n')
                tmp_set = tmp_set.union(r_serv.smembers(h).union(r_serv.smembers(tmp_h)))

            tmp_h = h

        F.write("\nSimilar Files:\n")

        for n, s in enumerate(tmp_set):

            F.write(str(n) + ': ' + s + '\n')

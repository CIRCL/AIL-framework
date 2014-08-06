import sys, hashlib, os, os.path, gzip, string, glob, itertools, copy, shutil
import redis, crcmod, mmh3, time, fileinput
import crcmod, mmh3

from operator import itemgetter, attrgetter
from pubsublogger import publisher




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



def select_hash(hashkind, line):
    """Select the kind of hashing for the line.

    :param hashkind: -- (str) The name of the hash
    :param line: -- (str) The string to hash.

    This function is a kind of hash selector which will use the hash passed
    in argument to hash the string also passed in argument.

    """
    if hashkind == "md5":
        hashline = hashlib.md5(line).hexdigest()

    elif hashkind == "sha1":
        hashline = hashlib.sha1(line).hexdigest()

    elif hashkind == "crc":
        crc32 = crcmod.Crc(0x104c11db7, initCrc=0, xorOut=0xFFFFFFFF)
        crc32.update(line)
        hashline = crc32.hexdigest()

    elif hashkind == "murmur":
        hashline = mmh3.hash(line)

    return str(hashline)




def redis_populate(pipe, folder, minline, hashkind, jmp, insert_type):
    """Call another function with different "mode"

    :param pipe: -- Redis pipe
    :param folder: -- the absolute path name to the folder where to process
    :param minline: -- the minimum lenght of line to hash
    :param hashkind: -- the hash to use
    :param jmp: -- (bool) trigger the jumping line mode or not
     :param insert_type: -- which kind of datastructure to create in redis.

     This Function actually call the function "insert_redis" with differents
     method to process it.
     In one way, x lines are jumped before the Insertion.
     In another, all the line are hashed and inserted in redis.

    """
    for filename in folder:

        with gzip.open(filename, 'rb') as F:
            start_line = 1

            for num, line in enumerate(F, start_line):

                if jmp != 1:

                    if (num % jmp) == 1 :
                        insert_redis(filename,
                            line,
                            pipe,
                            minline,
                            hashkind,
                            num,
                            insert_type)

                else:
                    insert_redis(filename,
                        line,
                        pipe,
                        minline,
                        hashkind,
                        num,
                        insert_type)

            pipe.execute()




def insert_redis(filename, line, pipe, minline, hashkind, num, insert_type):
    """Insert hashed line in redis.

    :param filename: -- the absolute path name to the folder where to process
    :param line: -- the clear line which will be hashed.
    :param pipe: -- Redis pipe
    :param minline: -- the minimum lenght of line to hash
    :param hashkind: -- the hash to use
    :param num: -- (int) the first line of the file (better human read)
    :param insert_type: -- (int) Choose the datastructure used in redis.

    This function insert hashed lines in the selected redis datastructure
    The datastructure is represented as follow:

    case one: ALLIN
    "hash"[hashedline][occurence] => to index all different hashs + scoring
    "hashedline"[filename.gz] => to associate the file.gz to his hashedline
    "L:hashedline"[clearline] => for the correspondance

    case two: SORTED SET (for the ./top.py script)
    "hash"[hashedline][occurence] => to index all different hashs + scoring
    "hashedline"[filename.gz] => to associate the file.gz to his hashedline

    case tree: BASIC SET (for ./Graph.py)
    "hash"[hashedline] to index all different hashs (without scores)
    "hashedline"[filename.gz] => to associate the file.gz to his hashedline
    "filename.gz"[firstline] => for human reading

    """
    if (insert_type == 2): # ALLIN
        if len(line) >= minline:

            pipe.zincrby("hash", select_hash(hashkind, line), 1)
            pipe.sadd(select_hash(hashkind,line), filename.split('/',20)[-1])
            pipe.sadd("L:"+select_hash(hashkind, line), clean(line))

            if (num == 1):

                pipe.sadd(filename.split('/',20)[-1], clean(line[0:80]))


    elif (insert_type == 1): # SORTED SET FOR TOP100.py

        if len(line) >= minline:

            pipe.zincrby("hash", select_hash(hashkind, line), 1)
            pipe.sadd(select_hash(hashkind, line), clean(line))


    elif (insert_type == 0): # SET FOR THE GRAPH

        if len(line) >= minline:

            pipe.sadd("hash", select_hash(hashkind, line))
            pipe.sadd(select_hash(hashkind,line), filename.split('/',20)[-1])

            if (num == 1):

                pipe.sadd(filename.split('/',20)[-1], clean(line[0:80]))




def remove_pure_doppelganger(r_serv, nb):
    """Remove identic paste

    :param r_serv: -- Redis connexion database
    :param nb: -- (int) Number of execution wanted

    Add to a temporary list the hash of wholes files and compare the new hash
    to the element of this list. If the hash is already inside, the file
    is deleted otherwise the hash is added in the list.

    """
    hashlist = []
    for x in xrange(0,nb):
        filename = r_serv.lpop("filelist")

        with open(filename, 'rb') as L:
            hashline = hashlib.md5(L.read()).hexdigest()

            print len(hashlist)

            if hashline in hashlist:

                os.remove(filename)
                publisher.debug("{0} removed".format(filename))
                print "{0} removed".format(filename)
            else:
                hashlist.append(hashline)

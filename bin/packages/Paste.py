#!/usr/bin/python3

"""
The ``Paste Class``
===================

Use it to create an object from an existing paste or other random file.

Conditions to fulfill to be able to use this class correctly:
-------------------------------------------------------------

1/ The paste need to be saved on disk somewhere (have an accessible path)
2/ The paste need to be gziped.
3/ The filepath need to look like something like this:
    /directory/source/year/month/day/paste.gz

"""

import os
import magic
import gzip
import redis
import operator
import string
import re
import json
import configparser
from io import StringIO
import sys
sys.path.append(os.path.join(os.environ['AIL_BIN'], 'packages/'))
from Date import Date
from Hash import Hash

from langid.langid import LanguageIdentifier, model

from nltk.tokenize import RegexpTokenizer
from textblob import TextBlob

clean = lambda dirty: ''.join(filter(string.printable.__contains__, dirty))
"""It filters out non-printable characters from the string it receives."""


class Paste(object):
    """
    This class representing a Paste as an object.
    When created, the object will have by default some "main attributes"
    such as the size or the date of the paste already calculated, whereas other
    attributes are not set and need to be "asked to be calculated" by their
    methods.
    It was design like this because some attributes take time to be calculated
    such as the langage or the duplicate...

    :Example:

    PST = Paste("/home/2013/01/12/ZEeGaez5.gz")

    """

    def __init__(self, p_path):

        configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
        if not os.path.exists(configfile):
            raise Exception('Unable to find the configuration file. \
                            Did you set environment variables? \
                            Or activate the virtualenv.')

        cfg = configparser.ConfigParser()
        cfg.read(configfile)
        self.cache = redis.StrictRedis(
            host=cfg.get("Redis_Queues", "host"),
            port=cfg.getint("Redis_Queues", "port"),
            db=cfg.getint("Redis_Queues", "db"),
            decode_responses=True)
        self.store = redis.StrictRedis(
            host=cfg.get("Redis_Data_Merging", "host"),
            port=cfg.getint("Redis_Data_Merging", "port"),
            db=cfg.getint("Redis_Data_Merging", "db"),
            decode_responses=True)
        self.store_metadata = redis.StrictRedis(
            host=cfg.get("ARDB_Metadata", "host"),
            port=cfg.getint("ARDB_Metadata", "port"),
            db=cfg.getint("ARDB_Metadata", "db"),
            decode_responses=True)

        self.p_path = p_path
        self.p_name = os.path.basename(self.p_path)
        self.p_size = round(os.path.getsize(self.p_path)/1024.0, 2)
        self.p_mime = magic.from_buffer("test", mime=True)
        self.p_mime = magic.from_buffer(self.get_p_content(), mime=True)

        # Assuming that the paste will alway be in a day folder which is itself
        # in a month folder which is itself in a year folder.
        # /year/month/day/paste.gz

        var = self.p_path.split('/')
        self.p_date = Date(var[-4], var[-3], var[-2])
        self.p_rel_path = os.path.join(var[-4], var[-3], var[-2], self.p_name)
        self.p_source = var[-5]
        self.supposed_url = 'https://{}/{}'.format(self.p_source.replace('_pro', ''), var[-1].split('.gz')[0])

        self.p_encoding = None
        self.p_hash_kind = {}
        self.p_hash = {}
        self.p_langage = None
        self.p_nb_lines = None
        self.p_max_length_line = None
        self.array_line_above_threshold = None
        self.p_duplicate = None
        self.p_tags = None

    def get_p_content(self):
        """
        Returning the content of the Paste

        :Example:

        PST.get_p_content()

        """

        paste = self.cache.get(self.p_path)
        if paste is None:
            try:
                with gzip.open(self.p_path, 'r') as f:
                    paste = f.read()
                    self.cache.set(self.p_path, paste)
                    self.cache.expire(self.p_path, 300)
            except:
                paste = ''

        return str(paste)

    def get_p_content_as_file(self):
        message = StringIO(self.get_p_content())
        return message

    def get_p_content_with_removed_lines(self, threshold):
        num_line_removed = 0
        line_length_threshold = threshold
        string_content = ""
        f = self.get_p_content_as_file()
        line_id = 0
        for line_id, line in enumerate(f):
            length = len(line)

            if length < line_length_threshold:
                string_content += line
            else:
                num_line_removed+=1

        return (num_line_removed, string_content)

    def get_lines_info(self):
        """
        Returning and setting the number of lines and the maximum lenght of the
        lines of the paste.

        :return: tuple (#lines, max_length_line)

        :Example: PST.get_lines_info()

        """
        if self.p_nb_lines is None or self.p_max_length_line is None:
            max_length_line = 0
            f = self.get_p_content_as_file()
            line_id = 0
            for line_id, line in enumerate(f):
                length = len(line)
                if length >= max_length_line:
                    max_length_line = length

            f.close()
            self.p_nb_lines = line_id
            self.p_max_length_line = max_length_line

        return (self.p_nb_lines, self.p_max_length_line)

    def _get_p_encoding(self):
        """
        Setting the encoding of the paste.

        :Example: PST._set_p_encoding()

        """
        return self.p_mime

    def _set_p_hash_kind(self, hashkind):
        """
        Setting the hash (as an object) used for futur operation on it.

        :Example: PST._set_p_hash_kind("md5")

        .. seealso:: Hash.py Object to get the available hashs.

        """
        self.p_hash_kind[hashkind] = (Hash(hashkind))

    def _get_p_hash(self):
        """
        Setting the hash of the paste as a kind of "uniq" identificator

        :return: a dictionnary of hash string (md5, sha1....)

        :Example: PST._get_p_hash()

        .. note:: You need first to "declare which kind of hash you want to use
        before using this function
        .. seealso:: _set_p_hash_kind("md5")

        """
        for hash_name, the_hash in self.p_hash_kind.items():
            self.p_hash[hash_name] = the_hash.Calculate(self.get_p_content().encode())
        return self.p_hash

    def _get_p_language(self):
        """
        Returning and setting the language of the paste (guessing)

        :Example: PST._get_p_language()

        ..note:: The language returned is purely guessing and may not be accurate
        if the paste doesn't contain any human dictionnary words
        ..seealso: git@github.com:saffsd/langid.py.git

        FIXME: This procedure is using more than 20% of CPU

	"""
        identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        return identifier.classify(self.get_p_content())

    def _get_p_hash_kind(self):
        return self.p_hash_kind

    def _get_p_date(self):
        return self.p_date

    def _get_p_size(self):
        return self.p_size

    def is_duplicate(self, obj, min=1, percent=50, start=1, jump=10):
        """
        Returning the percent of similarity with another paste.
        ( Using the previous hashing method )

        :param obj: (Paste) The paste to compare with
        :param min: -- (int) Minimum line length to be hashed.
        :param percent: -- (int)
        :param start: -- (int) Number the line where to start.
        :param jump: -- (int) Granularity of the hashing 0 or 1 means no jumps
        (Maximum Granularity)

        :return: (tuple) (bool, percent)

        :Example:
        PST.is_duplicate(PST)

        >>> return (True, 100.0)

        ..seealso: _get_hash_lines()

        """

        set1 = self._get_hash_lines(min, start, jump)
        set2 = obj._get_hash_lines(min, start, jump)

        inter = set.intersection(set1, set2)

        numerator = len(inter)
        denominator = float((len(set1) + len(set2)) / 2)

        try:
            var = round((numerator / denominator)*100, 2)
        except ZeroDivisionError:
            var = 0.0

        if var >= percent:
            return True, var
        else:
            return False, var

    def _get_p_duplicate(self):
        self.p_duplicate = self.store_metadata.smembers('dup:'+self.p_path)
        if self.p_duplicate is not None:
            return list(self.p_duplicate)
        else:
            return '[]'

    def _get_p_tags(self):
        self.p_tags = self.store_metadata.smembers('tag:'+path, tag)
        if self.self.p_tags is not None:
            return list(self.p_tags)
        else:
            return '[]'

    def get_p_rel_path(self):
        return self.p_rel_path

    def save_all_attributes_redis(self, key=None):
        """
        Saving all the attributes in a "Redis-like" Database (Redis, LevelDB)

        :param r_serv: -- Connexion to the Database.
        :param key: -- Key of an additionnal set.

        Example:
        import redis

        r_serv = redis.StrictRedis(host = 127.0.0.1, port = 6739, db = 0)

        PST = Paste("/home/Zkopkmlk.gz")
        PST.save_all_attributes_redis(r_serv)

        """
        # LevelDB Compatibility
        p = self.store.pipeline(False)
        p.hset(self.p_path, "p_name", self.p_name)
        p.hset(self.p_path, "p_size", self.p_size)
        p.hset(self.p_path, "p_mime", self.p_mime)
        # p.hset(self.p_path, "p_encoding", self.p_encoding)
        p.hset(self.p_path, "p_date", self._get_p_date())
        p.hset(self.p_path, "p_hash_kind", self._get_p_hash_kind())
        p.hset(self.p_path, "p_hash", self.p_hash)
        # p.hset(self.p_path, "p_langage", self.p_langage)
        # p.hset(self.p_path, "p_nb_lines", self.p_nb_lines)
        # p.hset(self.p_path, "p_max_length_line", self.p_max_length_line)
        # p.hset(self.p_path, "p_categories", self.p_categories)
        p.hset(self.p_path, "p_source", self.p_source)
        if key is not None:
            p.sadd(key, self.p_path)
        else:
            pass
        p.execute()

    def save_attribute_redis(self, attr_name, value):
        """
        Save an attribute as a field
        """
        if type(value) == set:
            self.store.hset(self.p_path, attr_name, json.dumps(list(value)))
        else:
            self.store.hset(self.p_path, attr_name, json.dumps(value))

    def save_attribute_duplicate(self, value):
        """
        Save an attribute as a field
        """
        for tuple in value:
            self.store_metadata.sadd('dup:'+self.p_path, tuple)

    def save_others_pastes_attribute_duplicate(self, list_value):
        """
        Save a new duplicate on others pastes
        """
        for hash_type, path, percent, date in list_value:
            to_add = (hash_type, self.p_path, percent, date)
            self.store_metadata.sadd('dup:'+path,to_add)

    def _get_from_redis(self, r_serv):
        ans = {}
        for hash_name, the_hash in self.p_hash:
            ans[hash_name] = r_serv.hgetall(the_hash)
        return ans

    def _get_top_words(self, sort=False):
        """
        Tokenising method: Returning a sorted list or a set of paste's words

        :param sort: Selecting the output: sorted list or a set. (set by default)

        :return: set or sorted list of tuple [(word, occurency)...]

        :Example: PST._get_top_words(False)

        """
        words = {}
        tokenizer = RegexpTokenizer('[\&\~\:\;\,\.\(\)\{\}\|\[\]\\\\/\-/\=\'\"\%\$\?\@\+\#\_\^\<\>\!\*\n\r\t\s]+',
                                    gaps=True, discard_empty=True)

        blob = TextBlob(clean( (self.get_p_content()) ), tokenizer=tokenizer)

        for word in blob.tokens:
            if word in words.keys():
                num = words[word]
            else:
                num = 0
            words[word] = num + 1
        if sort:
            var = sorted(words.items(), key=operator.itemgetter(1), reverse=True)
        else:
            var = words

        return var

    def _get_word(self, word):
        """
        Returning a specific word and his occurence if present in the paste

        :param word: (str) The word

        :return: (tuple) ("foo", 1337)

        """
        return [item for item in self._get_top_words() if item[0] == word]

    def get_regex(self, regex):
        """
        Returning matches with the regex given as an argument.

        :param regex: -- (str) a regex

        :return: (list)

        :Example: PST.get_regex("4[0-9]{12}(?:[0-9]{3})?")


        """
        matchs = []
        for match in re.findall(regex, self.get_p_content()):
            if match != '' and len(match) < 100:
                matchs.append(match)
        return matchs

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"""
The WebStats Module
======================

This module makes stats on URL recolted from the web module.
It consider the TLD, Domain and protocol.

"""

##################################
# Import External packages
##################################
import time
import datetime
import redis
import os
from pubsublogger import publisher
from pyfaup.faup import Faup


##################################
# Import Project packages
##################################
from module.abstract_module import AbstractModule
from packages import lib_words
from packages.Date import Date
from Helper import Process


class WebStats(AbstractModule):
    """
    WebStats module for AIL framework
    """

    # Config Var
    THRESHOLD_TOTAL_SUM = 200 # Above this value, a keyword is eligible for a progression
    THRESHOLD_INCREASE = 1.0  # The percentage representing the keyword occurence since num_day_to_look
    MAX_SET_CARDINALITY = 10  # The cardinality of the progression set
    NUM_DAY_TO_LOOK = 5       # the detection of the progression start num_day_to_look in the past


    def __init__(self):
        super(WebStats, self).__init__()

        # Send module state to logs
        self.redis_logger.info("Module %s initialized"%(self.module_name))
        # Sent to the logging a description of the module
        self.redis_logger.info("Makes statistics about valid URL")

        self.pending_seconds = 5*60

        # REDIS #
        self.r_serv_trend = redis.StrictRedis(
            host=self.process.config.get("ARDB_Trending", "host"),
            port=self.process.config.get("ARDB_Trending", "port"),
            db=self.process.config.get("ARDB_Trending", "db"),
            decode_responses=True)

        # FILE CURVE SECTION #
        self.csv_path_proto = os.path.join(os.environ['AIL_HOME'],
                                    self.process.config.get("Directories", "protocolstrending_csv"))
        self.protocolsfile_path = os.path.join(os.environ['AIL_HOME'],
                                    self.process.config.get("Directories", "protocolsfile"))

        self.csv_path_tld = os.path.join(os.environ['AIL_HOME'],
                                    self.process.config.get("Directories", "tldstrending_csv"))
        self.tldsfile_path = os.path.join(os.environ['AIL_HOME'],
                                    self.process.config.get("Directories", "tldsfile"))

        self.csv_path_domain = os.path.join(os.environ['AIL_HOME'],
                                    self.process.config.get("Directories", "domainstrending_csv"))

        self.faup = Faup()
        self.generate_new_graph = False


    def computeNone(self):
        if self.generate_new_graph:
            self.generate_new_graph = False

            today = datetime.date.today()
            year = today.year
            month = today.month

            self.redis_logger.debug('Building protocol graph')
            lib_words.create_curve_with_word_file(self.r_serv_trend, self.csv_path_proto,
                                                    self.protocolsfile_path, year,
                                                    month)

            self.redis_logger.debug('Building tld graph')
            lib_words.create_curve_with_word_file(self.r_serv_trend, self.csv_path_tld,
                                                    self.tldsfile_path, year,
                                                    month)

            self.redis_logger.debug('Building domain graph')
            lib_words.create_curve_from_redis_set(self.r_serv_trend, self.csv_path_domain,
                                                    "domain", year,
                                                    month)
            self.redis_logger.debug('end building')


    def compute(self, message):
        self.generate_new_graph = True

        # Do something with the message from the queue
        url, date, path = message.split()
        self.faup.decode(url)
        url_parsed = self.faup.get()

        # Scheme analysis
        self.analyse('scheme', date, url_parsed)
        # Tld analysis
        self.analyse('tld', date, url_parsed)
        # Domain analysis
        self.analyse('domain', date, url_parsed)

        self.compute_progression('scheme', self.NUM_DAY_TO_LOOK, url_parsed)
        self.compute_progression('tld', self.NUM_DAY_TO_LOOK, url_parsed)
        self.compute_progression('domain', self.NUM_DAY_TO_LOOK, url_parsed)


    def analyse(self, field_name, date, url_parsed):
        field = url_parsed[field_name]

        if field is not None:
            try: # faup version
                field = field.decode()
            except:
                pass

            self.r_serv_trend.hincrby(field, date, 1)

            if field_name == "domain": #save domain in a set for the monthly plot
                domain_set_name = "domain_set_" + date[0:6]
                self.r_serv_trend.sadd(domain_set_name, field)
                self.redis_logger.debug("added in " + domain_set_name +": "+ field)


    def get_date_range(self, num_day):
        curr_date = datetime.date.today()
        date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
        date_list = []

        for i in range(0, num_day+1):
            date_list.append(date.substract_day(i))
        return date_list


    def compute_progression_word(self, num_day, keyword):
        """
        Compute the progression for one keyword
        """
        date_range = self.get_date_range(num_day)
        # check if this keyword is eligible for progression
        keyword_total_sum = 0
        value_list = []
        for date in date_range: # get value up to date_range
            curr_value = self.r_serv_trend.hget(keyword, date)
            value_list.append(int(curr_value if curr_value is not None else 0))
            keyword_total_sum += int(curr_value) if curr_value is not None else 0
        oldest_value = value_list[-1] if value_list[-1] != 0 else 1 #Avoid zero division

        # The progression is based on the ratio: value[i] / value[i-1]
        keyword_increase = 0
        value_list_reversed = value_list[:]
        value_list_reversed.reverse()
        for i in range(1, len(value_list_reversed)):
            divisor = value_list_reversed[i-1] if value_list_reversed[i-1] != 0 else 1
            keyword_increase += value_list_reversed[i] / divisor

        return (keyword_increase, keyword_total_sum)


    def compute_progression(self, field_name, num_day, url_parsed):
        """
            recompute the set top_progression zset
                - Compute the current field progression
                - re-compute the current progression for each first 2*self.MAX_SET_CARDINALITY fields in the top_progression_zset
        """
        redis_progression_name_set = "z_top_progression_"+field_name

        keyword = url_parsed[field_name]
        if keyword is not None:

            #compute the progression of the current word
            keyword_increase, keyword_total_sum = self.compute_progression_word(num_day, keyword)

            #re-compute the progression of 2*self.MAX_SET_CARDINALITY
            current_top = self.r_serv_trend.zrevrangebyscore(redis_progression_name_set, '+inf', '-inf', withscores=True, start=0, num=2*self.MAX_SET_CARDINALITY)
            for word, value in current_top:
                word_inc, word_tot_sum = self.compute_progression_word(num_day, word)
                self.r_serv_trend.zrem(redis_progression_name_set, word)
                if (word_tot_sum > self.THRESHOLD_TOTAL_SUM) and (word_inc > self.THRESHOLD_INCREASE):
                    self.r_serv_trend.zadd(redis_progression_name_set, float(word_inc), word)

            # filter before adding
            if (keyword_total_sum > self.THRESHOLD_TOTAL_SUM) and (keyword_increase > self.THRESHOLD_INCREASE):
                self.r_serv_trend.zadd(redis_progression_name_set, float(keyword_increase), keyword)


if __name__ == '__main__':

    module = WebStats()
    module.run()

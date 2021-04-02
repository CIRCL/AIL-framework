#!/usr/bin/env python3
# -*-coding:UTF-8 -*
"""
    This module makes statistics for some modules and providers

"""

##################################
# Import External packages       #
##################################
import time
import datetime
import redis
import os


##################################
# Import Project packages        #
##################################
from module.abstract_module import AbstractModule
from packages.Date import Date
from pubsublogger import publisher
from Helper import Process
from packages import Paste
import ConfigLoader


class ModuleStats(AbstractModule):
    """
    Module Statistics module for AIL framework
    """

    # Config Var
    MAX_SET_CARDINALITY = 8


    def __init__(self):

        super(ModuleStats, self).__init__()

        # Waiting time in secondes between to message proccessed
        self.pending_seconds = 20

        # Sent to the logging a description of the module
        self.redis_logger.info("Makes statistics about valid URL")

        # REDIS #
        self.r_serv_trend = ConfigLoader.ConfigLoader().get_redis_conn("ARDB_Trending")

    def compute(self, message):

        if len(message.split(';')) > 1:
            self.compute_most_posted(message)
        else:
            self.compute_provider_info(message)


    def get_date_range(self, num_day):
        curr_date = datetime.date.today()
        date = Date(str(curr_date.year)+str(curr_date.month).zfill(2)+str(curr_date.day).zfill(2))
        date_list = []

        for i in range(0, num_day+1):
            date_list.append(date.substract_day(i))
        return date_list


    def compute_most_posted(self, message):
        module, num, keyword, paste_date = message.split(';')

        redis_progression_name_set = 'top_'+ module +'_set_' + paste_date

        # Add/Update in Redis
        self.r_serv_trend.hincrby(paste_date, module+'-'+keyword, int(num))

        # Compute Most Posted
        date = self.get_date_range(0)[0]
        # check if this keyword is eligible for progression
        keyword_total_sum = 0

        curr_value = self.r_serv_trend.hget(date, module+'-'+keyword)
        keyword_total_sum += int(curr_value) if curr_value is not None else 0

        if self.r_serv_trend.zcard(redis_progression_name_set) < self.MAX_SET_CARDINALITY:
            self.r_serv_trend.zadd(redis_progression_name_set, float(keyword_total_sum), keyword)

        else: # not in set
            member_set = self.r_serv_trend.zrangebyscore(redis_progression_name_set, '-inf', '+inf', withscores=True, start=0, num=1)
            # Member set is a list of (value, score) pairs
            if int(member_set[0][1]) < keyword_total_sum:
                #remove min from set and add the new one
                self.redis_logger.debug(module + ': adding ' +keyword+ '(' +str(keyword_total_sum)+') in set and removing '+member_set[0][0]+'('+str(member_set[0][1])+')')
                self.r_serv_trend.zrem(redis_progression_name_set, member_set[0][0])
                self.r_serv_trend.zadd(redis_progression_name_set, float(keyword_total_sum), keyword)
                self.redis_logger.debug(redis_progression_name_set)


    def compute_provider_info(self, message):
        redis_all_provider = 'all_provider_set'

        paste = Paste.Paste(message)

        paste_baseName = paste.p_name.split('.')[0]
        paste_size = paste._get_p_size()
        paste_provider = paste.p_source
        paste_date = str(paste._get_p_date())
        redis_sum_size_set = 'top_size_set_' + paste_date
        redis_avg_size_name_set = 'top_avg_size_set_' + paste_date
        redis_providers_name_set = 'providers_set_' + paste_date

        # Add/Update in Redis
        self.r_serv_trend.sadd(redis_all_provider, paste_provider)

        num_paste = int(self.r_serv_trend.hincrby(paste_provider+'_num', paste_date, 1))
        sum_size = float(self.r_serv_trend.hincrbyfloat(paste_provider+'_size', paste_date, paste_size))
        new_avg = float(sum_size) / float(num_paste)
        self.r_serv_trend.hset(paste_provider +'_avg', paste_date, new_avg)


        #
        # Compute Most Posted
        #

        # Size
        if self.r_serv_trend.zcard(redis_sum_size_set) < self.MAX_SET_CARDINALITY or self.r_serv_trend.zscore(redis_sum_size_set, paste_provider) != "nil":
            self.r_serv_trend.zadd(redis_sum_size_set, float(num_paste), paste_provider)
            self.r_serv_trend.zadd(redis_avg_size_name_set, float(new_avg), paste_provider)
        else: #set full capacity
            member_set = self.r_serv_trend.zrangebyscore(redis_sum_size_set, '-inf', '+inf', withscores=True, start=0, num=1)
            # Member set is a list of (value, score) pairs
            if float(member_set[0][1]) < new_avg:
                #remove min from set and add the new one
                self.redis_logger.debug('Size - adding ' +paste_provider+ '(' +str(new_avg)+') in set and removing '+member_set[0][0]+'('+str(member_set[0][1])+')')
                self.r_serv_trend.zrem(redis_sum_size_set, member_set[0][0])
                self.r_serv_trend.zadd(redis_sum_size_set, float(sum_size), paste_provider)
                self.r_serv_trend.zrem(redis_avg_size_name_set, member_set[0][0])
                self.r_serv_trend.zadd(redis_avg_size_name_set, float(new_avg), paste_provider)


        # Num
        # if set not full or provider already present
        if self.r_serv_trend.zcard(redis_providers_name_set) < self.MAX_SET_CARDINALITY or self.r_serv_trend.zscore(redis_providers_name_set, paste_provider) != "nil":
            self.r_serv_trend.zadd(redis_providers_name_set, float(num_paste), paste_provider)
        else: #set at full capacity
            member_set = self.r_serv_trend.zrangebyscore(redis_providers_name_set, '-inf', '+inf', withscores=True, start=0, num=1)
            # Member set is a list of (value, score) pairs
            if int(member_set[0][1]) < num_paste:
                #remove min from set and add the new one
                self.redis_logger.debug('Num - adding ' +paste_provider+ '(' +str(num_paste)+') in set and removing '+member_set[0][0]+'('+str(member_set[0][1])+')')
                self.r_serv_trend.zrem(member_set[0][0])
                self.r_serv_trend.zadd(redis_providers_name_set, float(num_paste), paste_provider)


if __name__ == '__main__':

    module = ModuleStats()
    module.run()

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import redis
import datetime

sys.path.append(os.path.join(os.environ['AIL_BIN'], 'lib'))
import ConfigLoader

config_loader = ConfigLoader.ConfigLoader()
r_serv_queues = config_loader.get_redis_conn("Redis_Queues")
config_loader = None

def get_all_queues_name():
    return r_serv_queues.hkeys('queues')

def get_all_queues_dict_with_nb_elem():
    return r_serv_queues.hgetall('queues')

def get_all_queues_with_sorted_nb_elem():
    res = r_serv_queues.hgetall('queues')
    res = sorted(res.items())
    return res

def get_module_pid_by_queue_name(queue_name):
    return r_serv_queues.smembers('MODULE_TYPE_{}'.format(queue_name))

# # TODO: remove last msg part
def get_module_last_process_start_time(queue_name, module_pid):
    res = r_serv_queues.get('MODULE_{}_{}'.format(queue_name, module_pid))
    if res:
        return res.split(',')[0]
    return None

def get_module_last_msg(queue_name, module_pid):
    return r_serv_queues.get('MODULE_{}_{}_PATH'.format(queue_name, module_pid))

def get_all_modules_queues_stats():
    all_modules_queues_stats = []
    for queue_name, nb_elem_queue in get_all_queues_with_sorted_nb_elem():
        l_module_pid = get_module_pid_by_queue_name(queue_name)
        for module_pid in l_module_pid:
            last_process_start_time = get_module_last_process_start_time(queue_name, module_pid)
            if last_process_start_time:
                last_process_start_time = datetime.datetime.fromtimestamp(int(last_process_start_time))
                seconds = int((datetime.datetime.now() - last_process_start_time).total_seconds())
            else:
                seconds = 0
            all_modules_queues_stats.append((queue_name, nb_elem_queue, seconds, module_pid))
    return all_modules_queues_stats

if __name__ == '__main__':
    res = get_all_modules_queues_stats()
    print(res)

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import datetime
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.exceptions import ModuleQueueError
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_queues = config_loader.get_redis_conn("Redis_Queues")
config_loader = None

MODULES_FILE = os.path.join(os.environ['AIL_HOME'], 'configs', 'modules.cfg')


class AILQueue:

    def __init__(self, module_name, module_pid):
        self.name = module_name
        self.pid = module_pid
        self._set_subscriber()
        # Update queue stat
        r_queues.hset('queues', self.name, self.get_nb_messages())
        r_queues.hset(f'modules', f'{self.pid}:{self.name}', -1)

    def _set_subscriber(self):
        subscribers = {}
        module_config_loader = ConfigLoader(config_file=MODULES_FILE)  # TODO CHECK IF FILE EXISTS
        if not module_config_loader.has_section(self.name):
            raise ModuleQueueError(f'No Section defined for this module: {self.name}. Please add one in configs/module.cfg')

        if module_config_loader.has_option(self.name, 'publish'):
            subscribers_queues = module_config_loader.get_config_str(self.name, 'publish')
            if subscribers_queues:
                subscribers_queues = set(subscribers_queues.split(','))
                for queue_name in subscribers_queues:
                    subscribers[queue_name] = set()
                if subscribers_queues:
                    for module in module_config_loader.get_config_sections():
                        if module_config_loader.has_option(module, 'subscribe'):
                            queue_name = module_config_loader.get_config_str(module, 'subscribe')
                            if queue_name in subscribers:
                                subscribers[queue_name].add(module)
        self.subscribers_modules = subscribers

    def get_nb_messages(self):
        return r_queues.llen(f'queue:{self.name}:in')

    def get_message(self):
        # Update queues stats
        r_queues.hset('queues', self.name, self.get_nb_messages())
        r_queues.hset(f'modules', f'{self.pid}:{self.name}', int(time.time()))
        # Get Message
        message = r_queues.lpop(f'queue:{self.name}:in')
        if not message:
            return None
        else:
            # TODO SAVE CURRENT ITEMS (OLD Module information)

            return message

    def send_message(self, message, queue_name=None):
        if not self.subscribers_modules:
            raise ModuleQueueError('This Module don\'t have any subscriber')
        if queue_name:
            if queue_name not in self.subscribers_modules:
                raise ModuleQueueError(f'send_message: Unknown queue_name {queue_name}')
        else:
            if len(self.subscribers_modules) > 1:
                raise ModuleQueueError('Queue name required. This module push to multiple queues')
            queue_name = list(self.subscribers_modules)[0]

        # Add message to all modules
        for module_name in self.subscribers_modules[queue_name]:
            r_queues.rpush(f'queue:{module_name}:in', message)
            # stats
            nb_mess = r_queues.llen(f'queue:{module_name}:in')
            r_queues.hset('queues', module_name, nb_mess)

    # TODO
    def refresh(self):
        # TODO check cache
        self._set_subscriber()

    def clear(self):
        r_queues.delete(f'queue:{self.name}:in')

    def error(self):
        r_queues.hdel(f'modules', f'{self.pid}:{self.name}')

def get_queues_modules():
    return r_queues.hkeys('queues')

def get_nb_queues_modules():
    return r_queues.hgetall('queues')

def get_nb_sorted_queues_modules():
    res = r_queues.hgetall('queues')
    res = sorted(res.items())
    return res

def get_modules_pid_last_mess():
    return r_queues.hgetall('modules')

def get_modules_queues_stats():
    modules_queues_stats = []
    nb_queues_modules = get_nb_queues_modules()
    modules_pid_last_mess = get_modules_pid_last_mess()
    added_modules = set()
    for row_module in modules_pid_last_mess:
        pid, module = row_module.split(':', 1)
        last_time = modules_pid_last_mess[row_module]
        last_time = datetime.datetime.fromtimestamp(int(last_time))
        seconds = int((datetime.datetime.now() - last_time).total_seconds())
        modules_queues_stats.append((module, nb_queues_modules[module], seconds, pid))
        added_modules.add(module)
    for module in nb_queues_modules:
        if module not in added_modules:
            modules_queues_stats.append((module, nb_queues_modules[module], -1, 'Not Launched'))
    return sorted(modules_queues_stats)

def clear_modules_queues_stats():
    r_queues.delete('modules')

def get_queue_digraph():
    queues_ail = {}
    modules = {}
    module_config_loader = ConfigLoader(config_file=MODULES_FILE)
    for module in module_config_loader.get_config_sections():
        if module_config_loader.has_option(module, 'subscribe'):
            if module not in modules:
                modules[module] = {'in': set(), 'out': set()}
            queue = module_config_loader.get_config_str(module, 'subscribe')
            modules[module]['in'].add(queue)
            if queue not in queues_ail:
                queues_ail[queue] = []
            queues_ail[queue].append(module)

        if module_config_loader.has_option(module, 'publish'):
            if module not in modules:
                modules[module] = {'in': set(), 'out': set()}
            queues = module_config_loader.get_config_str(module, 'publish')
            for queue in queues.split(','):
                modules[module]['out'].add(queue)

    # print(modules)
    # print(queues_ail)

    mapped = set()
    import_modules = set()
    edges = '# Define edges between nodes\n'
    for module in modules:
        for queue_name in modules[module]['out']:
            if queue_name == 'Importers':
                import_modules.add(module)
            if queue_name in queues_ail:
                for module2 in queues_ail[queue_name]:
                    to_break = False
                    new_edge = None
                    cluster_out = f'cluster_{queue_name.lower()}'
                    queue_in = modules[module]['in']
                    if queue_in:
                        queue_in = next(iter(queue_in))
                        if len(queues_ail.get(queue_in, [])) == 1:
                            cluster_in = f'cluster_{queue_in.lower()}'
                            new_edge = f'{module} -> {module2} [ltail="{cluster_in}" lhead="{cluster_out}"];\n'
                            to_break = True
                    if not new_edge:
                        new_edge = f'{module} -> {module2} [lhead="{cluster_out}"];\n'
                    to_map = f'{module}:{cluster_out}'
                    if to_map not in mapped:
                        mapped.add(to_map)
                        edges = f'{edges}{new_edge}'
                    if to_break:
                        break

    subgraph = '# Define subgraphs for each queue\n'
    for queue_name in queues_ail:
        cluster_name = f'cluster_{queue_name.lower()}'
        subgraph = f'{subgraph}  subgraph {cluster_name} {{\n    label="Queue {queue_name}";\n    color=blue;\n'
        for module in queues_ail[queue_name]:
            subgraph = f'{subgraph}    {module};\n'
        subgraph = f'{subgraph}}}\n\n'

    cluster_name = f'cluster_importers'
    subgraph = f'{subgraph}  subgraph {cluster_name} {{\n    label="AIL Importers";\n    color=red;\n'
    for module in import_modules:
        subgraph = f'{subgraph}    {module};\n'
    subgraph = f'{subgraph}}}\n\n'

    digraph = 'digraph Modules {\ngraph [rankdir=LR splines=ortho];\nnode [shape=rectangle]\ncompound=true;\n'
    digraph = f'{digraph}edge[arrowhead=open color=salmon]\n\n'
    digraph = f'{digraph}{subgraph}{edges}\n}}\n'
    return digraph

def save_queue_digraph():
    import subprocess
    digraph = get_queue_digraph()
    dot_file = os.path.join(os.environ['AIL_HOME'], 'doc/ail_queues.dot')
    svg_file = os.path.join(os.environ['AIL_HOME'], 'doc/ail_queues.svg')
    with open(dot_file, 'w') as f:
        f.write(digraph)

    print('dot', '-Tsvg', dot_file, '-o', svg_file)
    process = subprocess.run(['dot', '-Tsvg', dot_file, '-o', svg_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        # modified_files = process.stdout
        # print(process.stdout)
        return True
    else:
        print(process.stderr.decode())
        sys.exit(1)


###########################################################################################
###########################################################################################
###########################################################################################
###########################################################################################
###########################################################################################

# def get_all_queues_name():
#     return r_queues.hkeys('queues')
#
# def get_all_queues_dict_with_nb_elem():
#     return r_queues.hgetall('queues')
#
# def get_all_queues_with_sorted_nb_elem():
#     res = r_queues.hgetall('queues')
#     res = sorted(res.items())
#     return res
#
# def get_module_pid_by_queue_name(queue_name):
#     return r_queues.smembers('MODULE_TYPE_{}'.format(queue_name))
#
# # # TODO: remove last msg part
# def get_module_last_process_start_time(queue_name, module_pid):
#     res = r_queues.get('MODULE_{}_{}'.format(queue_name, module_pid))
#     if res:
#         return res.split(',')[0]
#     return None
#
# def get_module_last_msg(queue_name, module_pid):
#     return r_queues.get('MODULE_{}_{}_PATH'.format(queue_name, module_pid))
#
# def get_all_modules_queues_stats():
#     all_modules_queues_stats = []
#     for queue_name, nb_elem_queue in get_all_queues_with_sorted_nb_elem():
#         l_module_pid = get_module_pid_by_queue_name(queue_name)
#         for module_pid in l_module_pid:
#             last_process_start_time = get_module_last_process_start_time(queue_name, module_pid)
#             if last_process_start_time:
#                 last_process_start_time = datetime.datetime.fromtimestamp(int(last_process_start_time))
#                 seconds = int((datetime.datetime.now() - last_process_start_time).total_seconds())
#             else:
#                 seconds = 0
#             all_modules_queues_stats.append((queue_name, nb_elem_queue, seconds, module_pid))
#     return all_modules_queues_stats
#
#
# def _get_all_messages_from_queue(queue_name):
#     #self.r_temp.hset('queues', self.subscriber_name, int(self.r_temp.scard(in_set)))
#     return r_queues.smembers(f'queue:{queue_name}:in')
#
# # def is_message_in queue(queue_name):
# #     pass
#
# def remove_message_from_queue(queue_name, message):
#     queue_key = f'queue:{queue_name}:in'
#     r_queues.srem(queue_key, message)
#     r_queues.hset('queues', queue_name, int(r_queues.scard(queue_key)))


if __name__ == '__main__':
    # clear_modules_queues_stats()
    save_queue_digraph()

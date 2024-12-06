#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import datetime
import time

import xxhash

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.exceptions import ModuleQueueError
from lib.ConfigLoader import ConfigLoader
from lib import ail_core

config_loader = ConfigLoader()
r_queues = config_loader.get_redis_conn("Redis_Queues")
r_obj_process = config_loader.get_redis_conn("Redis_Process")
timeout_queue_obj = 172800
config_loader = None

MODULES_FILE = os.path.join(os.environ['AIL_HOME'], 'configs', 'modules.cfg')

# # # # # # # #
#             #
#  AIL QUEUE  #
#             #
# # # # # # # #

class AILQueue:

    def __init__(self, module_name, module_pid):
        self.name = module_name
        self.pid = module_pid
        self._set_subscriber()
        # Update queue stat
        r_queues.hset('queues', self.name, self.get_nb_messages())

        r_queues.sadd('modules', self.name)
        r_queues.hset(f'module:{self.name}', self.pid, -1)

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

    def get_out_queues(self):
        return list(self.subscribers_modules.keys())

    def get_nb_messages(self):
        return r_queues.llen(f'queue:{self.name}:in')

    def get_message(self):
        # Update queues stats
        r_queues.hset('queues', self.name, self.get_nb_messages())
        r_queues.hset(f'module:{self.name}', self.pid, int(time.time()))

        # Get Message
        message = r_queues.lpop(f'queue:{self.name}:in')
        if not message:
            return None
        else:
            row_mess = message.split(';', 1)
            if len(row_mess) != 2:
                return None, None, message
                # raise Exception(f'Error: queue {self.name}, no AIL object provided')
            else:
                obj_global_id, mess = row_mess
                m_hash = xxhash.xxh3_64_hexdigest(message)
                add_processed_obj(obj_global_id, m_hash, module=self.name)
                return obj_global_id, m_hash, mess

    def rename_message_obj(self, new_id, old_id):
        # restrict rename function
        if self.name == 'Mixer' or self.name == 'Global':
            rename_processed_obj(new_id, old_id)
        else:
            raise ModuleQueueError('This Module can\'t rename an object ID')

        # condition -> not in any queue
        # TODO EDIT meta

    def end_message(self, obj_global_id, m_hash):
        end_processed_obj(obj_global_id, m_hash, module=self.name)

    def send_message(self, obj_global_id, message='', queue_name=None):
        if not self.subscribers_modules:
            raise ModuleQueueError('This Module don\'t have any subscriber')
        if queue_name:
            if queue_name not in self.subscribers_modules:
                raise ModuleQueueError(f'send_message: Unknown queue_name {queue_name}')
        else:
            if len(self.subscribers_modules) > 1:
                raise ModuleQueueError('Queue name required. This module push to multiple queues')
            queue_name = list(self.subscribers_modules)[0]

        message = f'{obj_global_id};{message}'
        if obj_global_id != '::':
            m_hash = xxhash.xxh3_64_hexdigest(message)
        else:
            m_hash = None

        # Add message to all modules
        for module_name in self.subscribers_modules[queue_name]:
            if m_hash:
                add_processed_obj(obj_global_id, m_hash, queue=module_name)

            r_queues.rpush(f'queue:{module_name}:in', message)
            # stats
            nb_mess = r_queues.llen(f'queue:{module_name}:in')
            r_queues.hset('queues', module_name, nb_mess)

    def start(self):
        r_queues.hset(f'module:start:{self.name}', self.pid, int(time.time()))

    # TODO
    def refresh(self):
        # TODO check cache
        self._set_subscriber()

    def clear(self):
        r_queues.delete(f'queue:{self.name}:in')

    def _stop_module(self):
        r_queues.hdel(f'module:{self.name}', self.pid)
        if r_queues.hlen(f'module:{self.name}') == 0:
            r_queues.srem('modules', self.name)

    def error(self):
        self._stop_module

    def end(self):
        self.clear()
        self._stop_module()


def get_queues_modules():
    return r_queues.hkeys('queues')

def get_nb_queues_modules():
    return r_queues.hgetall('queues')

def get_nb_sorted_queues_modules():
    res = r_queues.hgetall('queues')
    res = sorted(res.items())
    return res

def get_modules_names():
    return r_queues.smembers('modules')

def get_module_pids(name):
    return r_queues.hkeys(f'module:{name}')

def get_module_start_time(name, pid):
    return r_queues.hget(f'module:start:{name}', pid)

def get_module_last_time(name, pid):
    return r_queues.hget(f'module:{name}', pid)

def get_modules_queues_stats():  # TODO ADD OPTION TO PURGE QUEUES
    stats = {}
    modules_names = sorted(get_modules_names())
    nb_queues_modules = get_nb_queues_modules()
    for name in modules_names:
        modules = {}
        for pid in get_module_pids(name):
            modules[pid] = {'start': get_module_start_time(name, pid), 'last': get_module_last_time(name, pid)}
        stats[name] = {'in': nb_queues_modules[name], 'modules': modules}

    # Check if module not started
    for name in nb_queues_modules:
        if name not in stats:
            stats[name] = {'in': nb_queues_modules[name], 'modules': None}
    return stats

def clear_modules_queues_stats():
    for name in get_modules_names():
        r_queues.delete(f'module:{name}')
    r_queues.delete('modules')


# # # # # # # # #
#               #
#  OBJ QUEUES   # PROCESS ??
#               #
# # # # # # # # #


def get_processed_objs():
    return r_obj_process.smembers(f'objs:process')

def get_processed_end_objs():
    return r_obj_process.smembers(f'objs:processed')

def get_processed_end_obj():
    return r_obj_process.spop(f'objs:processed')

def is_obj_in_process(obj_gid):
    return r_obj_process.sismember(f'objs:process', obj_gid)

def get_processed_objs_by_type(obj_type):
    return r_obj_process.zrange(f'objs:process:{obj_type}', 0, -1)

def is_processed_obj_queued(obj_global_id):
    return r_obj_process.exists(f'obj:queues:{obj_global_id}')

def is_processed_obj_moduled(obj_global_id):
    return r_obj_process.exists(f'obj:modules:{obj_global_id}')

def is_processed_obj(obj_global_id):
    return is_processed_obj_queued(obj_global_id) or is_processed_obj_moduled(obj_global_id)

def get_processed_obj_modules(obj_global_id):
    return r_obj_process.zrange(f'obj:modules:{obj_global_id}', 0, -1)

def get_processed_obj_queues(obj_global_id):
    return r_obj_process.zrange(f'obj:queues:{obj_global_id}', 0, -1)

def get_processed_obj(obj_global_id):
    return {'modules': get_processed_obj_modules(obj_global_id), 'queues': get_processed_obj_queues(obj_global_id)}

def add_processed_obj(obj_global_id, m_hash, module=None, queue=None):
    obj_type = obj_global_id.split(':', 1)[0]
    new_obj = r_obj_process.sadd(f'objs:process', obj_global_id)
    # first process:
    if new_obj:
        r_obj_process.zadd(f'objs:process:{obj_type}', {obj_global_id: int(time.time())})
    if queue:
        r_obj_process.zadd(f'obj:queues:{obj_global_id}', {f'{queue}:{m_hash}': int(time.time())})
    if module:
        r_obj_process.zadd(f'obj:modules:{obj_global_id}', {f'{module}:{m_hash}': int(time.time())})
        r_obj_process.zrem(f'obj:queues:{obj_global_id}', f'{module}:{m_hash}')

def end_processed_obj(obj_global_id, m_hash, module=None, queue=None):
    if queue:
        r_obj_process.zrem(f'obj:queues:{obj_global_id}', f'{queue}:{m_hash}')
    if module:
        r_obj_process.zrem(f'obj:modules:{obj_global_id}', f'{module}:{m_hash}')

        # TODO HANDLE QUEUE DELETE
        # process completed
        if not is_processed_obj(obj_global_id):
            obj_type = obj_global_id.split(':', 1)[0]
            r_obj_process.zrem(f'objs:process:{obj_type}', obj_global_id)
            r_obj_process.srem(f'objs:process', obj_global_id)

            r_obj_process.sadd(f'objs:processed', obj_global_id)   # TODO use list ??????

def rename_processed_obj(new_id, old_id):
    module = get_processed_obj_modules(old_id)
    # currently in a module
    if len(module) == 1:
        module, x_hash = module[0].split(':', 1)
        obj_type = old_id.split(':', 1)[0]
        r_obj_process.zrem(f'obj:modules:{old_id}', f'{module}:{x_hash}')
        r_obj_process.zrem(f'objs:process:{obj_type}', old_id)
        r_obj_process.srem(f'objs:process', old_id)
        add_processed_obj(new_id, x_hash, module=module)

def get_last_queue_timeout():
    epoch_update = r_obj_process.get('queue:obj:timeout:last')
    if not epoch_update:
        epoch_update = 0
    return float(epoch_update)

def timeout_process_obj(obj_global_id):
    for q in get_processed_obj_queues(obj_global_id):
        queue, x_hash = q.split(':', 1)
        r_obj_process.zrem(f'obj:queues:{obj_global_id}', f'{queue}:{x_hash}')
    for m in get_processed_obj_modules(obj_global_id):
        module, x_hash = m.split(':', 1)
        r_obj_process.zrem(f'obj:modules:{obj_global_id}', f'{module}:{x_hash}')

    obj_type = obj_global_id.split(':', 1)[0]
    r_obj_process.zrem(f'objs:process:{obj_type}', obj_global_id)
    r_obj_process.srem(f'objs:process', obj_global_id)

    r_obj_process.sadd(f'objs:processed', obj_global_id)
    print(f'timeout: {obj_global_id}')


def timeout_processed_objs():
    curr_time = int(time.time())
    time_limit = curr_time - timeout_queue_obj
    for obj_type in ail_core.get_obj_queued():
        for obj_global_id in r_obj_process.zrangebyscore(f'objs:process:{obj_type}', 0, time_limit):
            timeout_process_obj(obj_global_id)
    r_obj_process.set('queue:obj:timeout:last', time.time())

def delete_processed_obj(obj_global_id):
    for q in get_processed_obj_queues(obj_global_id):
        queue, x_hash = q.split(':', 1)
        r_obj_process.zrem(f'obj:queues:{obj_global_id}', f'{queue}:{x_hash}')
    for m in get_processed_obj_modules(obj_global_id):
        module, x_hash = m.split(':', 1)
        r_obj_process.zrem(f'obj:modules:{obj_global_id}', f'{module}:{x_hash}')
    obj_type = obj_global_id.split(':', 1)[0]
    r_obj_process.zrem(f'objs:process:{obj_type}', obj_global_id)
    r_obj_process.srem(f'objs:process', obj_global_id)

###################################################################################


# # # # # # # #
#             #
#    GRAPH    #
#             #
# # # # # # # #

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
    svg_static = os.path.join(os.environ['AIL_HOME'], 'var/www/static/image/ail_queues.svg')
    with open(dot_file, 'w') as f:
        f.write(digraph)

    print('dot', '-Tsvg', dot_file, '-o', svg_file)
    process = subprocess.run(['dot', '-Tsvg', dot_file, '-o', svg_file, '-o', svg_static], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode == 0:
        # modified_files = process.stdout
        # print(process.stdout)
        return True
    else:
        print(process.stderr.decode())
        sys.exit(1)


if __name__ == '__main__':
    # print(get_processed_end_objs())
    print(get_modules_queues_stats())

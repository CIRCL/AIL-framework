#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from uuid import uuid4

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
r_meta = config_loader.get_db_conn("Kvrocks_Timeline")
config_loader = None

# CORRELATION_TYPES_BY_OBJ = {
#     "chat": ["item", "username"],  # item ???
#     "cookie-name": ["domain"],
#     "cryptocurrency": ["domain", "item"],
#     "cve": ["domain", "item"],
#     "decoded": ["domain", "item"],
#     "domain": ["cve", "cookie-name", "cryptocurrency", "decoded", "etag", "favicon", "hhhash", "item", "pgp", "title", "screenshot", "username"],
#     "etag": ["domain"],
#     "favicon": ["domain", "item"],
#     "hhhash": ["domain"],
#     "item": ["chat", "cve", "cryptocurrency", "decoded", "domain", "favicon", "pgp", "screenshot", "title", "username"],
#     "pgp": ["domain", "item"],
#     "screenshot": ["domain", "item"],
#     "title": ["domain", "item"],
#     "username": ["chat", "domain", "item"],
# }
#
# def get_obj_correl_types(obj_type):
#     return CORRELATION_TYPES_BY_OBJ.get(obj_type)

# def sanityze_obj_correl_types(obj_type, correl_types):
#     obj_correl_types = get_obj_correl_types(obj_type)
#     if correl_types:
#         correl_types = set(correl_types).intersection(obj_correl_types)
#     if not correl_types:
#         correl_types = obj_correl_types
#         if not correl_types:
#             return []
#     return correl_types

class Timeline:

    def __init__(self, global_id, name):
        self.id = global_id
        self.name = name

    def _get_block_obj_global_id(self, block):
        return r_meta.hget(f'block:{self.id}:{self.name}', block)

    def _set_block_obj_global_id(self, block, global_id):
        return r_meta.hset(f'block:{self.id}:{self.name}', block, global_id)

    def _get_block_timestamp(self, block, position):
        return r_meta.zscore(f'line:{self.id}:{self.name}', f'{position}:{block}')

    def _get_nearest_bloc_inf(self, timestamp):
        inf = r_meta.zrevrangebyscore(f'line:{self.id}:{self.name}', float(timestamp), 0, start=0, num=1, withscores=True)
        if inf:
            inf, score = inf[0]
            if inf.startswith('end'):
                inf_key = f'start:{inf[4:]}'
                inf_score = r_meta.zscore(f'line:{self.id}:{self.name}', inf_key)
                if inf_score == score:
                    inf = inf_key
            return inf
        else:
            return None

    def _get_nearest_bloc_sup(self, timestamp):
        sup = r_meta.zrangebyscore(f'line:{self.id}:{self.name}', float(timestamp), '+inf', start=0, num=1, withscores=True)
        if sup:
            sup, score = sup[0]
            if sup.startswith('start'):
                sup_key = f'end:{sup[6:]}'
                sup_score = r_meta.zscore(f'line:{self.id}:{self.name}', sup_key)
                if score == sup_score:
                    sup = sup_key
            return sup
        else:
            return None

    def get_first_obj_id(self):
        first = r_meta.zrange(f'line:{self.id}:{self.name}', 0, 0)
        if first:  # start:block
            first = first[0]
            if first.startswith('start:'):
                first = first[6:]
            else:
                first = first[4:]
            return self._get_block_obj_global_id(first)

    def get_last_obj_id(self):
        last = r_meta.zrevrange(f'line:{self.id}:{self.name}', 0, 0)
        if last:  # end:block
            last = last[0]
            if last.startswith('end:'):
                last = last[4:]
            else:
                last = last[6:]
            return self._get_block_obj_global_id(last)

    def get_objs_ids(self):
        objs = set()
        for block in r_meta.zrange(f'line:{self.id}:{self.name}', 0, -1):
            if block:
                if block.startswith('start:'):
                    print(self._get_block_obj_global_id(block[6:]))
                    objs.add(self._get_block_obj_global_id(block[6:]))
        return objs

    def get_objs(self):
        objs = []
        blocks = r_meta.zrange(f'line:{self.id}:{self.name}', 0, -1, withscores=True)
        for i in range(0, len(blocks), 2):
            block1, score1 = blocks[i]
            block2, score2 =blocks[i + 1]
            score1 = int(score1)
            score2 = int(score2)
            if block1.startswith('start:'):
                start = score1
                end = score2
                obj = self._get_block_obj_global_id(block1[6:])
            else:
                start = score2
                end = score1
                obj = self._get_block_obj_global_id(block2[6:])
            objs.append({'obj': obj, 'start': start, 'end': end})
        return objs

    # def get_objs_ids(self):
    #     objs = {}
    #     last_obj_id = None
    #     for block, timestamp in r_meta.zrange(f'line:{self.id}:{self.name}', 0, -1, withscores=True):
    #         if block:
    #             if block.startswith('start:'):
    #                 last_obj_id = self._get_block_obj_global_id(block[6:])
    #                 objs[last_obj_id] = {'first_seen': timestamp}
    #             else:
    #                 objs[last_obj_id]['last_seen'] = timestamp
    #     return objs

    def _update_bloc(self, block, position, timestamp):
        r_meta.zadd(f'line:{self.id}:{self.name}', {f'{position}:{block}': timestamp})

    def _add_bloc(self, obj_global_id, timestamp, end=None):
        if end:
            timestamp_end = end
        else:
            timestamp_end = timestamp
        new_bloc = str(uuid4())
        r_meta.zadd(f'line:{self.id}:{self.name}', {f'start:{new_bloc}': timestamp, f'end:{new_bloc}': timestamp_end})
        self._set_block_obj_global_id(new_bloc, obj_global_id)
        return new_bloc

    def add_timestamp(self, timestamp, obj_global_id):
        inf = self._get_nearest_bloc_inf(timestamp)
        sup = self._get_nearest_bloc_sup(timestamp)
        if not inf and not sup:
            # create new bloc
            new_bloc = self._add_bloc(obj_global_id, timestamp)
            return new_bloc
        # timestamp < first_seen
        elif not inf:
            sup_pos, sup_id = sup.split(':')
            sup_obj = self._get_block_obj_global_id(sup_id)
            if sup_obj == obj_global_id:
                self._update_bloc(sup_id, 'start', timestamp)
            # create new bloc
            else:
                new_bloc = self._add_bloc(obj_global_id, timestamp)
                return new_bloc

        # timestamp > first_seen
        elif not sup:
            inf_pos, inf_id = inf.split(':')
            inf_obj = self._get_block_obj_global_id(inf_id)
            if inf_obj == obj_global_id:
                self._update_bloc(inf_id, 'end', timestamp)
            # create new bloc
            else:
                new_bloc = self._add_bloc(obj_global_id, timestamp)
                return new_bloc

        else:
            inf_pos, inf_id = inf.split(':')
            sup_pos, sup_id = sup.split(':')
            inf_obj = self._get_block_obj_global_id(inf_id)

            if inf_id == sup_id:
                # reduce bloc + create two new bloc
                if obj_global_id != inf_obj:
                    # get end timestamp
                    sup_timestamp = self._get_block_timestamp(sup_id, 'end')
                    # reduce original bloc
                    self._update_bloc(inf_id, 'end', timestamp - 1)
                    # Insert new bloc
                    new_bloc = self._add_bloc(obj_global_id, timestamp)
                    # Recreate end of the first bloc by a new bloc
                    self._add_bloc(inf_obj, timestamp + 1, end=sup_timestamp)
                    return new_bloc

                # timestamp in existing bloc
                else:
                    return inf_id

            # different blocs: expend sup/inf bloc or create a new bloc if
            elif inf_pos == 'end' and sup_pos == 'start':
                # Extend inf bloc
                if obj_global_id == inf_obj:
                    self._update_bloc(inf_id, 'end', timestamp)
                    return inf_id

                sup_obj = self._get_block_obj_global_id(sup_id)
                # Extend sup bloc
                if obj_global_id == sup_obj:
                    self._update_bloc(sup_id, 'start', timestamp)
                    return sup_id

                # create new bloc
                new_bloc = self._add_bloc(obj_global_id, timestamp)
                return new_bloc

            # inf_pos == 'start' and sup_pos == 'end'
            # else raise error ???

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reindex Meilisearch data from AIL.

By default, this script indexes one or more datasets without deleting existing
indexes. If `--reset` is provided, it first deletes and recreates all indexes.
In both cases, index creation/configuration is ensured before indexing starts.
"""

import argparse
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import search_engine

def ensure_indexes_ready(reset=False):
    """Ensure indexes exist and are configured before indexing."""
    engine = search_engine.Engine

    if reset:
        engine._delete_all()
        engine.create_indexes()
    else:
        existing = set(engine.get_indexes())
        required = set(search_engine.get_indexes_names())
        for index_name in sorted(required - existing):
            engine._create_index(index_name)
            engine.setup_indexes_searchable_filterable_sortable()


def run_indexing(index_type):
    indexing_fct = search_engine.INDEXING_FUNCTIONS[index_type]
    indexing_fct()


def parse_args():
    parser = argparse.ArgumentParser(
        description='Optionally reset Meilisearch indexes and index one dataset or everything.'
    )
    parser.add_argument(
        '-t',
        '--type',
        dest='index_type',
        default='all',
        choices=sorted(search_engine.INDEXING_FUNCTIONS.keys()),
        help='Dataset type to index (default: all)',
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Delete and recreate all indexes before indexing',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.reset:
        print('Resetting indexes and preparing configuration...')
    else:
        print('Preparing indexes and configuration (no reset)...')

    if not search_engine.is_meilisearch_enabled():
        raise RuntimeError('Meilisearch is disabled in configuration')

    if not search_engine.Engine.is_up():
        raise RuntimeError('Meilisearch is not reachable')

    ensure_indexes_ready(reset=args.reset)
    print('Indexes are ready.')

    print(f'Start indexing: {args.index_type}')
    run_indexing(args.index_type)
    print('Indexing finished.')


if __name__ == '__main__':
    main()

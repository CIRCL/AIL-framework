#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of AIL framework - Analysis Information Leak framework
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Copyright (c) 2014 Alexandre Dulaunoy - a@foo.be

import configparser
import argparse
import gzip
import os


def readdoc(path=None):
    if path is None:
        return False
    f = gzip.open(path, 'r')
    return f.read()

configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
cfg = configparser.ConfigParser()
cfg.read(configfile)

# Indexer configuration - index dir and schema setup
indexpath = os.path.join(os.environ['AIL_HOME'], cfg.get("Indexer", "path"))
indexertype = cfg.get("Indexer", "type")

argParser = argparse.ArgumentParser(description='Fulltext search for AIL')
argParser.add_argument('-q', action='append', help='query to lookup (one or more)')
argParser.add_argument('-n', action='store_true', default=False, help='return numbers of indexed documents')
argParser.add_argument('-t', action='store_true', default=False, help='dump top 500 terms')
argParser.add_argument('-l', action='store_true', default=False, help='dump all terms encountered in indexed documents')
argParser.add_argument('-f', action='store_true', default=False, help='dump each matching document')
argParser.add_argument('-v', action='store_true', default=False, help='Include filepath')
argParser.add_argument('-s', action='append', help='search similar documents')

args = argParser.parse_args()

from whoosh import index
from whoosh.fields import Schema, TEXT, ID

schema = Schema(title=TEXT(stored=True), path=ID(stored=True), content=TEXT)

ix = index.open_dir(indexpath)

from whoosh.qparser import QueryParser

if args.n:
    print(ix.doc_count_all())
    exit(0)

if args.l:
    xr = ix.searcher().reader()
    for x in xr.lexicon("content"):
        print (x)
    exit(0)

if args.t:
    xr = ix.searcher().reader()
    for x in xr.most_frequent_terms("content", number=500, prefix=''):
        print (x)
    exit(0)

if args.s:
    # By default, the index is not storing the vector of the document (Whoosh
    # document schema). It won't work if you don't change the schema of the
    # index for the content. It depends of your storage strategy.
    docnum = ix.searcher().document_number(path=args.s)
    r = ix.searcher().more_like(docnum, "content")
    for hit in r:
            print(hit["path"])
    exit(0)

if args.q is None:
    argParser.print_help()
    exit(1)

with ix.searcher() as searcher:
    query = QueryParser("content", ix.schema).parse(" ".join(args.q))
    results = searcher.search(query, limit=None)
    for x in results:
        if args.f:
            if args.v:
                print (x.items()[0][1])
            print (readdoc(path=x.items()[0][1]))
        else:
            print (x.items()[0][1])
        print

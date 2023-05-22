#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIR/File Importer Helper
================

Import Content

"""

import argparse
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from importer import FileImporter


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Directory or file importer')
    parser.add_argument('-d', '--directory', type=str, help='Root directory to import')
    parser.add_argument('-f', '--file', type=str, help='File to import')
    args = parser.parse_args()

    if not args.directory and not args.file:
        parser.print_help()
        sys.exit(0)

    if args.directory:
        dir_path = args.directory
        dir_importer = FileImporter.DirImporter()
        dir_importer.importer(dir_path)

    if args.file:
        file_path = args.file
        file_importer = FileImporter.FileImporter()
        file_importer.importer(file_path)

#!/usr/bin/env python3
"""Audit or rebuild AIL geolocation indexes without altering valid observations."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin'))

from lib import geo_engine


def main():
    parser = argparse.ArgumentParser(description='Audit GEO records/indexes; pause object and GEO mutations before applying repairs.')
    parser.add_argument('--apply', action='store_true', help='Rebuild indexes and remove stale references; default is a read-only audit.')
    parser.add_argument('--remove-orphans', action='store_true', help='Also remove canonical records whose AIL object no longer exists; only writes with --apply.')
    args = parser.parse_args()

    from lib.objects import ail_objects

    def owner_exists(obj_gid):
        obj_type, subtype, obj_id = obj_gid.split(':', 2)
        if not ail_objects.is_valid_object_type(obj_type):
            return False
        return ail_objects.exists_obj(obj_type, subtype, obj_id)

    report = geo_engine.repair_geo_indexes(apply=args.apply, owner_exists=owner_exists, remove_orphans=args.remove_orphans)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report['error_count'] else 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sys

sys.path.append(os.environ['AIL_BIN'])

from lib.ConfigLoader import ConfigLoader
from lib import Language
from lib.objects import Messages

logger = logging.getLogger('ail.language_migration')


def migrate_message_languages(r_lang, dry_run=False):
    counters = {
        'already_valid_bcp47': 0,
        'migrated_iso639_3': 0,
        'normalized_bcp47': 0,
        'skipped_invalid': 0,
        'updated_messages': 0,
    }

    for key in r_lang.scan_iter(match='obj:lang:message:*'):
        message_id = key.split(':', 3)[-1]
        message = Messages.Message(message_id)
        existing_languages = list(message.get_languages())
        if not existing_languages:
            continue

        changed = False
        for language in existing_languages:
            target = None
            category = None

            iso_migrated = Language.iso639_3_to_bcp47_primary(language)
            if iso_migrated:
                target = iso_migrated
                if target == language:
                    category = 'already_valid_bcp47'
                else:
                    category = 'migrated_iso639_3'
            else:
                canonical = Language.normalize_bcp47_tag(language)
                if canonical:
                    target = canonical
                    category = 'already_valid_bcp47' if canonical == language else 'normalized_bcp47'
                else:
                    counters['skipped_invalid'] += 1
                    logger.warning('Skipping invalid/unmappable language tag for %s: %s', message.get_global_id(), language)
                    continue

            counters[category] += 1
            if target == language:
                continue

            changed = True
            if dry_run:
                logger.info('Would migrate %s language %s -> %s', message.get_global_id(), language, target)
                continue

            message.remove_language(language)
            message.add_language(target)
            logger.info('Migrated %s language %s -> %s', message.get_global_id(), language, target)

        if changed:
            counters['updated_messages'] += 1

    return counters


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    dry_run = '--dry-run' in sys.argv

    config_loader = ConfigLoader()
    r_lang = config_loader.get_db_conn('Kvrocks_Languages')

    counters = migrate_message_languages(r_lang, dry_run=dry_run)
    logger.info('Migration summary: %s', counters)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sys

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import Language
from lib import chats_viewer

logger = logging.getLogger('ail.language_migration')


def migrate_message_languages(dry_run=False):
    nb_messages = chats_viewer.get_nb_messages_iterator()
    nb_done = 0
    counters = {
        'already_valid_bcp47': 0,
        'migrated_iso639_3': 0,
        'normalized_bcp47': 0,
        'skipped_invalid': 0,
        'updated_messages': 0,
    }

    for message in chats_viewer.get_messages_iterator():
        # progress
        if nb_done % 10000 == 0:
            progress = int((nb_done * 100) / nb_messages)
            logger.info(f'{progress}% {nb_done}/{nb_messages}')

        existing_languages = list(message.get_languages())
        if not existing_languages:
            nb_done += 1
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
                    logger.warning(f'Skipping invalid/unmappable language tag for {message.get_global_id()}: {language}')
                    continue

            counters[category] += 1
            if target == language:
                continue

            changed = True
            if dry_run:
                logger.info(f'Migrate {message.id} language {language} -> {target}')
                continue

            message.remove_language(language)
            message.add_language(target)
            logger.info(f'Migrated {message.id} language {language} -> {target}')

        if changed:
            counters['updated_messages'] += 1
        nb_done += 1
    return counters


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    dry_run = '--dry-run' in sys.argv

    counters = migrate_message_languages(dry_run=dry_run)
    logger.info(f'Migration summary: {counters}')


if __name__ == '__main__':
    main()

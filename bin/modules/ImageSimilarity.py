#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

from PIL import Image as PILImage
from PIL import UnidentifiedImageError

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib import image_similarity
from modules.abstract_module import AbstractModule


class ImageSimilarity(AbstractModule):

    def __init__(self):
        config_loader = ConfigLoader()
        self.phash_enabled = config_loader.get_config_boolean('ImageSimilarity', 'phash_enabled')
        self.photodna_enabled = config_loader.get_config_boolean('ImageSimilarity', 'photodna_enabled')

        super().__init__()
        self.enabled = self.phash_enabled or self.photodna_enabled
        self.pending_seconds = 1
        if self.enabled:
            self.logger.info(f'Module {self.module_name} initialized')
        else:
            self.logger.info(f'Module {self.module_name} disabled: no fingerprint algorithm is enabled')

    def compute(self, message, r_result=False):
        if not self.enabled:
            return None

        image = self.get_obj()
        if not image or image.type != 'image' or not image.exists():
            return None

        missing_phash = self.phash_enabled and not image_similarity.exists(image.id, image_similarity.PHASH)
        missing_photodna = self.photodna_enabled and not image_similarity.exists(image.id, image_similarity.PHOTODNA)
        if not missing_phash and not missing_photodna:
            if r_result:
                return image_similarity.get_fingerprints(image.id)
            return None

        try:
            with PILImage.open(image.get_filepath()) as decoded_image:
                if image_similarity.is_animated(decoded_image):
                    self.logger.info(f'Animated image skipped: {image.id}')
                    return None

                fingerprints = {}
                if missing_phash:
                    try:
                        fingerprints[image_similarity.PHASH] = image_similarity.calculate_phash(decoded_image)
                    except Exception as err:
                        self.logger.warning(f'Unable to calculate pHash for image {image.id}: {err}')

                if missing_photodna:
                    try:
                        fingerprints[image_similarity.PHOTODNA] = image_similarity.calculate_photodna(decoded_image)
                    except Exception as err:
                        self.logger.warning(f'Unable to calculate PhotoDNA for image {image.id}: {err}')
        except (OSError, UnidentifiedImageError) as err:
            self.logger.info(f'Invalid image {image.id}: {err}')
            return None

        for algorithm, fingerprint in fingerprints.items():
            image_similarity.set_fingerprint(image.id, algorithm, fingerprint)

        if r_result:
            return fingerprints
        return None


if __name__ == '__main__':
    module = ImageSimilarity()
    module.run()

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import base64
import magic
import os
import sys

from hashlib import sha256
from io import BytesIO

from flask import url_for
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects

config_loader = ConfigLoader()
r_serv_metadata = config_loader.get_db_conn("Kvrocks_Objects")
IMAGE_FOLDER = config_loader.get_files_directory('images')
config_loader = None


class Image(AbstractDaterangeObject):
    """
    AIL Screenshot Object. (strings)
    """

    # ID = SHA256
    def __init__(self, image_id):
        super(Image, self).__init__('image', image_id)

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True),
    #                 'compress': 'gzip'}
    #     return payload

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    def exists(self):
        return os.path.isfile(self.get_filepath())

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type=self.type, id=self.id)
        else:
            url = f'/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'far', 'icon': '\uf03e', 'color': '#E1F5DF', 'radius': 5}

    def get_rel_path(self):
        rel_path = os.path.join(self.id[0:2], self.id[2:4], self.id[4:6], self.id[6:8], self.id[8:10], self.id[10:12], self.id[12:])
        return rel_path

    def get_filepath(self):
        filename = os.path.join(IMAGE_FOLDER, self.get_rel_path())
        return os.path.realpath(filename)

    def is_gif(self, filepath=None):
        if not filepath:
            filepath = self.get_filepath()
        mime = magic.from_file(filepath, mime=True)
        if mime == 'image/gif':
            return True
        return False

    def get_file_content(self):
        filepath = self.get_filepath()
        with open(filepath, 'rb') as f:
            file_content = BytesIO(f.read())
        return file_content

    def get_content(self, r_type='str'):
        if r_type == 'str':
            return None
        else:
            return self.get_file_content()

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('file')

        obj_attrs.append(obj.add_attribute('sha256', value=self.id))
        obj_attrs.append(obj.add_attribute('attachment', value=self.id, data=self.get_file_content()))
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        meta['img'] = self.id
        meta['tags'] = self.get_tags(r_list=True)
        if 'content' in options:
            meta['content'] = self.get_content()
        if 'tags_safe' in options:
            meta['tags_safe'] = self.is_tags_safe(meta['tags'])
        return meta

    def create(self, content):
        filepath = self.get_filepath()
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filepath, 'wb') as f:
            f.write(content)

def get_screenshot_dir():
    return IMAGE_FOLDER

def get_all_images():
    images = []
    for root, dirs, files in os.walk(get_screenshot_dir()):
        for file in files:
            path = f'{root}{file}'
            image_id = path.replace(IMAGE_FOLDER, '').replace('/', '')
            images.append(image_id)
    return images


def get_all_images_objects(filters={}):
    for image_id in get_all_images():
        yield Image(image_id)


def create(content, size_limit=5000000, b64=False, force=False):
    size = (len(content)*3) / 4
    if size <= size_limit or size_limit < 0 or force:
        if b64:
            content = base64.standard_b64decode(content.encode())
        image_id = sha256(content).hexdigest()
        image = Image(image_id)
        if not image.exists():
            image.create(content)
        return image


class Images(AbstractDaterangeObjects):
    """
        CookieName Objects
    """
    def __init__(self):
        super().__init__('image', Image)

    def get_name(self):
        return 'Images'

    def get_icon(self):
        return {'fas': 'fas', 'icon': 'image'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_image.objects_images')
        else:
            url = f'{baseurl}/objects/images'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search  # TODO


# if __name__ == '__main__':
#     print(json.dumps(get_all_images()))
#     name_to_search = '29ba'
#     print(search_screenshots_by_name(name_to_search))

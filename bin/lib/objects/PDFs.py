#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import base64
import os
import sys
import pymupdf
import html2text

from io import BytesIO
from flask import url_for
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects
from lib import Language
# from lib.ail_core import get_default_image_description_model

config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache", decode_responses=False)
r_serv_metadata = config_loader.get_db_conn("Kvrocks_Objects")
PDF_FOLDER = os.path.join(config_loader.get_files_directory('files'), 'pdf')
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


class PDF(AbstractDaterangeObject):
    """
    AIL PDF Object.
    """

    # ID = SHA256
    def __init__(self, obj_id):
        super(PDF, self).__init__('pdf', obj_id)

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
            url = url_for('objects_pdf.pdf_view', id=self.id)
        else:
            url = f'/pdf/view?id={self.id}'
        return url

    def get_svg_icon(self):
        return {'style': 'far', 'icon': '\uf1c1', 'color': '#cc6600', 'radius': 5}

    def get_rel_path(self):
        rel_path = os.path.join(self.id[0:2], self.id[2:4], self.id[4:6], self.id[6:8], self.id[8:10], self.id[10:12], self.id[12:])
        return rel_path

    def get_filepath(self):
        filename = os.path.join(PDF_FOLDER, self.get_rel_path())
        return os.path.realpath(filename)

    def get_file_content(self):
        filepath = self.get_filepath()
        with open(filepath, 'rb') as f:
            file_content = BytesIO(f.read())
        return file_content

    def get_base64(self):
        return base64.b64encode(self.get_file_content().read()).decode()

    def get_content(self, r_type='str'):
        if r_type == 'str':
            return None
        else:
            return self.get_file_content()

    def get_markdown_id(self):
        return self.get_correlation('item').get('item', []).pop()[1:]

    def get_author(self):
        return self.get_correlation('author').get('author', []).pop()[1:]

    def get_file_names(self):
        file_names = []
        for f in self.get_correlation('file-name').get('file-name', []):
            file_names.append(f[1:])
        return file_names

    def get_misp_object(self):  # TODO
        obj_attrs = []
        obj = MISPObject('file')

        obj_attrs.append(obj.add_attribute('sha256', value=self.id))
        obj_attrs.append(obj.add_attribute('attachment', value=self.id, data=self.get_file_content()))
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    def get_meta(self, options=set(), flask_context=False):
        meta = self._get_meta(options=options, flask_context=flask_context)
        meta['id'] = self.id
        meta['tags'] = self.get_tags(r_list=True)
        if 'content' in options:
            meta['content'] = self.get_content()
        if 'tags_safe' in options:
            meta['tags_safe'] = self.is_tags_safe(meta['tags'])
        if 'author' in options:
            meta['author'] = self.get_author()
        if 'file-names' in options:
            meta['file-names'] = self.get_file_names()
        if 'markdown_id' in options:
            meta['markdown_id'] = self.get_markdown_id()
        return meta

    def translate(self, source, target):  # TODO harmonize
        g_id = self.get_global_id()
        translated = r_cache.get(f'translation:{source}:{target}:{g_id}:pdf')
        if translated:
            r_cache.expire(f'translation:{source}:{target}:{g_id}:pdf', 300)
            return translated

        doc = pymupdf.open(self.get_filepath())
        ocg_xref = doc.add_ocg("Translated", on=True)
        h = html2text.HTML2Text()
        h.ignore_links = True
        for page in doc:
            blocks = page.get_text('blocks', flags=pymupdf.TEXT_DEHYPHENATE)
            for block in blocks:
                bbox = block[:4]
                original = block[4]
                _, translated = Language.translate(original, source=source, target=target)
                page.draw_rect(bbox, color=None, fill=pymupdf.pdfcolor['white'], oc=ocg_xref)
                # html2text change new lines and list numbers
                translated = translated.replace('\n', '\\n')
                translated = h.handle(translated.strip()).replace('\\n', '<br>').replace('\n', ' ').replace('\\.', '.')
                page.insert_htmlbox(bbox, translated, oc=ocg_xref)
        translated = doc.tobytes(garbage=0, deflate=True)
        r_cache.set(f'translation:{source}:{target}:{g_id}:pdf', translated)
        r_cache.expire(f'translation:{source}:{target}:{g_id}:pdf', 300)
        return translated

    def create(self, content):
        filepath = self.get_filepath()
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filepath, 'wb') as f:
            f.write(content)


def get_all_pdfs():
    objs = []
    for root, dirs, files in os.walk(PDF_FOLDER):
        for file in files:
            path = f'{root}{file}'
            obj_id = path.replace(PDF_FOLDER, '').replace('/', '')
            objs.append(obj_id)
    return objs


def get_all_pdfs_objects(filters={}):
    for obj_id in get_all_pdfs():
        yield PDF(obj_id)

# obj_id -> original pdf sha256
def create(obj_id, content, size_limit=10000000, b64=False, force=False):
    size = (len(content)*3) / 4
    if size <= size_limit or size_limit < 0 or force:
        if b64:
            content = base64.standard_b64decode(content.encode())
        obj = PDF(obj_id)
        if not obj.exists():
            obj.create(content)
        return obj

def api_get_meta(obj_id, options=set(), flask_context=False):
    obj = PDF(obj_id)
    if not obj.exists():
        return {'error': 'PDF Not Found'}, 400
    return obj.get_meta(options=options, flask_context=flask_context), 200

def api_get_translation(obj_id, source, target):  # TODO check source, target
    obj = PDF(obj_id)
    if not obj.exists():
        return {'error': 'PDF Not Found'}, 404
    return obj.translate(source, target), 200

class PDFs(AbstractDaterangeObjects):
    """
        PDF Objects
    """
    def __init__(self):
        super().__init__('pdf', PDF)

    def get_name(self):
        return 'PDFS'

    def get_icon(self):
        return {'fas': 'far', 'icon': 'file-pdf'}

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('objects_pdf.objects_pdfs')
        else:
            url = f'{baseurl}/objects/pdfs'
        return url

    def sanitize_id_to_search(self, name_to_search):
        return name_to_search  # TODO


# if __name__ == '__main__':
#     pdf.translate()
#     print(time.time() - t)

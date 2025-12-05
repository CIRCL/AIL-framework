#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import base64
import os
import sys
import time

import pymupdf
import html2text

from io import BytesIO
from shapely.geometry import box
from flask import url_for
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_daterange_object import AbstractDaterangeObject, AbstractDaterangeObjects
from lib import Language
from packages import Date
# from lib.ail_core import get_default_image_description_model

config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache", decode_responses=False)
r_serv_metadata = config_loader.get_db_conn("Kvrocks_Objects")
PDF_FOLDER = os.path.join(config_loader.get_files_directory('files'), 'pdf')
PDF_MAX_SIZE = config_loader.get_config_int('Directories', 'max_pdf_size')  # bytes
PDF_TRANSLATED_DIR = config_loader.get_files_directory('translated_pdf')
if not os.path.isdir(PDF_TRANSLATED_DIR):
    os.makedirs(PDF_TRANSLATED_DIR)
PDF_TRANSLATED_TTL = config_loader.get_config_int('Directories', 'pdf_translation_ttl')
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


def is_bboxs_overlapping(bbox1, bbox2):
    b1 = box(0, bbox1[1], 1, bbox1[3] - 2)
    b2 = box(0, bbox2[1], 1, bbox2[3])
    return b1.intersects(b2)


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
        author = self.get_correlation('author').get('author', [])
        if author:
            return author.pop()[1:]
        return None

    def get_file_names(self):
        file_names = []
        for f in self.get_correlation('file-name').get('file-name', []):
            file_names.append(f[1:])
        return file_names

    def get_translated(self, language_name=False):
        obj_gid = self.get_global_id()
        translated = Language.get_obj_translated(obj_gid, language_name=language_name)
        task = Language.get_object_tasks(obj_gid, language_name=language_name)
        return {'translated': translated, 'task': task}

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
        if 'translated' in options:
            meta['translated'] = self.get_translated(language_name=True)
        return meta

    def translate(self, task, source, target):  # TODO harmonize

        filename = Language.exists_object_translation_language(self.get_global_id(), target)
        if filename:
            return filename

        doc = pymupdf.open(self.get_filepath())
        done = 0
        total = doc.page_count
        ocg_xref = doc.add_ocg("Translated", on=True)
        ocg_tab = doc.add_ocg("Table", on=True)
        h = html2text.HTML2Text()
        h.ignore_links = True

        # p = 0
        for page in doc:
            # p += 1
            # if p != 31:
            #     continue
            tabs = page.find_tables()  # detect the tables
            tabs_extracted = {}
            html_box_tables = []
            for tab in tabs:
                # print(tab)
                rows_text = tab.extract()
                # check if is a real table
                nb_cell = 0
                none_column = False
                for column in rows_text:
                    nb_column = 0
                    for v in column:
                        if v:
                            nb_column += 1
                    if nb_column < 1:
                        none_column = True
                        break
                    else:
                        nb_cell += nb_column
                if nb_cell > 1 and not none_column:
                    tabs_extracted[str(tab.bbox)] = rows_text
                    current_row = 0
                    # table coord -> tab.bbox
                    for row in tab.rows:
                        i = 0
                        for cell in row.cells:
                            if cell:
                                original = rows_text[current_row][i]
                                if original:
                                    _, translated = Language.translate(original.strip(), source=source, target=target, filter_same_content=False)
                                    if translated:
                                        translated = translated.strip()
                                    if translated:
                                        translated = translated.replace('\n', '\\n')
                                        translated = h.handle(translated.strip()).replace('\\n', '<br>').replace('\n', ' ').replace('\\.', '.')
                                        html_box_tables.append((cell, translated))
                            i += 1
                        current_row += 1
                # TODO TAB HEADERS
                # print(tab.header.external)
                # if tab.header.external:
                #     print('EXTERNAL --------------------------------')
                #     print(tab.header.bbox)
                #     print(tab.header.names)
                #     for cell in tab.header.cells:
                #         print(cell)

            blocks = page.get_text('blocks', flags=pymupdf.TEXT_DEHYPHENATE)
            for block in blocks:
                bbox = block[:4]
                original = block[4]
                if original:
                    original = "\n".join(" ".join(line.split()) for line in original.splitlines())
                    original = original.strip()
                    original = original.replace(' \n', '\n')
                    is_overlapping = False
                    if tabs and original:
                        l_overlapp = []
                        for tab in tabs:
                            if str(tab.bbox) in tabs_extracted:
                                # tab y <=
                                # text in table
                                if tab.bbox[1] <= bbox[1] and bbox[3] <= tab.bbox[3] + 2:
                                    is_overlapping = True
                                    break
                                if is_bboxs_overlapping(tab.bbox, bbox):
                                    l_overlapp.append(tab)
                        if len(l_overlapp) == 1:
                            tab = l_overlapp[0]
                            # filter start + end
                            if tab.bbox[1] > bbox[1] + 2 and tab.bbox[3] < bbox[3] - 2:
                                pass

                            # Text start
                            elif tab.bbox[1] > bbox[1]:
                                tab_extract = tabs_extracted[str(tab.bbox)][0][0]
                                if tab_extract:
                                    if original.startswith(tab_extract):
                                        is_overlapping = True
                                    else:
                                        y2 = tab.bbox[1] - 1
                                        original = original.split(tab_extract, 1)[0]
                                        if original:
                                            original = original.strip()
                                        bbox = (bbox[0], bbox[1], bbox[2], y2)
                            # Text end
                            elif tab.bbox[3] < bbox[3]:
                                tab_extract = tabs_extracted[str(tab.bbox)][-1][-1]
                                if tab_extract:
                                    if original.endswith(tab_extract):
                                        is_overlapping = True
                                    else:
                                        original = original.rsplit(tab_extract, 1)[1]
                                        y1 = tab.bbox[3] + 1
                                        bbox = (bbox[0], y1, bbox[2], bbox[3])
                            else:
                                is_overlapping = True

                        elif len(l_overlapp) == 2:
                            first_tab = None
                            last_tab = None
                            for tab in l_overlapp:
                                if tab.bbox[1] < bbox[1] and tab.bbox[3] < bbox[3]:
                                    first_tab = tab.bbox
                                elif tab.bbox[1] > bbox[1] and tab.bbox[3] < bbox[3]:
                                    last_tab = tab.bbox
                            if first_tab and last_tab:
                                # remove first tab
                                first_tab_last_cell = tabs_extracted[str(first_tab)][-1][-1]
                                if first_tab_last_cell:
                                    original = original.split(first_tab_last_cell, 1)[1]
                                    if original:
                                        original = original.strip()
                                    bbox = (bbox[0], first_tab[3] + 1, bbox[2], bbox[3])
                                # remove last tab
                                last_tab_first_row = tabs_extracted[str(last_tab)][0]
                                last_tab_first_row = ['' if x is None else x for x in last_tab_first_row]
                                last_tab_first_row = '\n'.join(last_tab_first_row)
                                if last_tab_first_row:
                                    original = original.rsplit(last_tab_first_row)[0]
                                    bbox = (bbox[0], bbox[1], bbox[2], last_tab[1] - 1)

                    if not is_overlapping and original:
                        _, translated = Language.translate(original, source=source, target=target)
                        page.draw_rect(bbox, color=None, fill=pymupdf.pdfcolor['white'], oc=ocg_xref)
                        # print(translated)
                        if translated:
                            translated = translated.strip()
                        if translated:
                            translated = translated.replace('\n', '\\n')
                            translated = h.handle(translated.strip()).replace('\\n', '<br>').replace('\n', ' ').replace('\\.', '.')
                            page.draw_rect(bbox, color=None, fill=pymupdf.pdfcolor['white'], oc=ocg_xref)
                            page.insert_htmlbox(bbox, translated, oc=ocg_xref)

            # add table
            if html_box_tables:
                for cell, translated in html_box_tables:
                    page.draw_rect(cell, color=None, fill=pymupdf.pdfcolor['white'], oc=ocg_tab)
                    page.insert_htmlbox(cell, translated, oc=ocg_tab)
            done += 1
            print(done)
            task.update_progress(done, total)

        print(task)

        # Save translated PDF
        # translated = doc.tobytes(garbage=0, deflate=True)
        filename = f'{target}_{int(time.time())}_{self.id}.pdf'
        doc.ez_save(os.path.join(PDF_TRANSLATED_DIR, filename))
        # doc.subset_fonts()  ???? reduce size ???
        # doc.ez_save("orca-korean.pdf")

        task.complete(filename)
        return filename

    def delete_translated(self, target):
        obj_gid = self.get_global_id()
        filename = Language.get_object_translation_language(obj_gid, target)
        if filename:
            Language.delete_obj_translation(obj_gid, target)
            os.remove(os.path.join(PDF_TRANSLATED_DIR, filename))

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
def create(obj_id, content, size_limit=PDF_MAX_SIZE, b64=False, force=False):
    size = (len(content)*3) / 4
    if size <= size_limit or size_limit < 0 or force:
        if b64:
            content = base64.standard_b64decode(content.encode())
        obj = PDF(obj_id)
        if not obj.exists():
            obj.create(content)
        return obj

def delete_translated_pdfs():
    for filename in os.listdir(PDF_TRANSLATED_DIR):
        if os.path.isfile(os.path.join(PDF_TRANSLATED_DIR, filename)):
            target, t, obj_id = filename.split('_', 2)
            obj_id = obj_id[:-4]
            print('deleted:', filename)
            Language.delete_obj_translation(f'pdf::{obj_id}', target)
            os.remove(os.path.join(PDF_TRANSLATED_DIR, filename))

def ttl_translated_pdfs():
    for filename in os.listdir(PDF_TRANSLATED_DIR):
        if os.path.isfile(os.path.join(PDF_TRANSLATED_DIR, filename)):
            target, t, obj_id = filename.split('_', 2)
            t = int(t)
            obj_id = obj_id[:-4]
            nb = Date.get_nb_days_by_daterange(Date.get_date_from_timestamp(t), Date.get_today_date_str())
            if nb >= PDF_TRANSLATED_TTL:
                print('deleted:', filename)
                Language.delete_obj_translation(f'pdf::{obj_id}', target)
                os.remove(os.path.join(PDF_TRANSLATED_DIR, filename))

def api_get_meta(obj_id, options=set(), flask_context=False):
    obj = PDF(obj_id)
    if not obj.exists():
        return {'error': 'PDF Not Found'}, 404
    return obj.get_meta(options=options, flask_context=flask_context), 200

def api_exists_translation_file(filename):
    filename = os.path.basename(filename)
    if not os.path.isfile(os.path.join(PDF_TRANSLATED_DIR, filename)):
        return {'error': 'No Translation Found or Expired. Please Launch a new translation'}, 404
    return filename, 200

def api_create_translation_task(obj_id, source, target, force=False):
    obj = PDF(obj_id)
    if not obj.exists():
        return {'error': 'PDF Not Found'}, 404
    if not Language.exists_lang_iso_target_source(source, target):
        return {'error': 'Invalid Language code'}, 400
    obj_gid = obj.get_global_id()
    if Language.exists_object_translation_language(obj_gid, target):
        if force:
            obj.delete_translated(target)
        else:
            return {'error': 'Already Translated'}, 400
    task_uuid = Language.create_translation_task(obj_gid, source, target, force=force)
    return task_uuid, 200

def api_get_translations_progress(obj_id):
    obj = PDF(obj_id)
    if not obj.exists():
        return {'error': 'PDF Not Found'}, 404
    return Language.api_get_object_translation_tasks_progress(Language.get_object_tasks_uuid(obj.get_global_id()))

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

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import magic
import requests
import zipfile

from flask import url_for
from io import BytesIO
from pymisp import MISPObject

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_daterange_object import AbstractDaterangeObject
from packages import Date

sys.path.append('../../configs/keys')
try:
    from virusTotalKEYS import vt_key
    if vt_key != '':
        VT_TOKEN = vt_key
        VT_ENABLED = True
        # print('VT submission is enabled')
    else:
        VT_ENABLED = False
        # print('VT submission is disabled')
except:
    VT_TOKEN = None
    VT_ENABLED = False
    # print('VT submission is disabled')

config_loader = ConfigLoader()
r_objects = config_loader.get_db_conn("Kvrocks_Objects")

HASH_DIR = config_loader.get_config_str('Directories', 'hash')
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


################################################################################
################################################################################
################################################################################

# # TODO: COMPLETE CLASS

class Decoded(AbstractDaterangeObject):
    """
    AIL Decoded Object. (strings)
    """

    def __init__(self, id):
        super(Decoded, self).__init__('decoded', id)

    # def get_ail_2_ail_payload(self):
    #     payload = {'raw': self.get_gzip_content(b64=True),
    #                 'compress': 'gzip'}
    #     return payload

    # # WARNING: UNCLEAN DELETE /!\ TEST ONLY /!\
    def delete(self):
        # # TODO:
        pass

    def get_link(self, flask_context=False):
        if flask_context:
            url = url_for('correlation.show_correlation', type="decoded", id=self.id)
        else:
            url = f'{baseurl}/correlation/show?type={self.type}&id={self.id}'
        return url

    def get_svg_icon(self, mimetype=None):
        if not mimetype:
            mimetype = self.get_mimetype()
        file_type = mimetype.split('/')[0]
        if file_type == 'application':
            icon = '\uf15b'
        elif file_type == 'audio':
            icon = '\uf1c7'
        elif file_type == 'image':
            icon = '\uf1c5'
        elif file_type == 'text':
            icon = '\uf15c'
        else:
            icon = '\uf249'
        return {'style': 'fas', 'icon': icon, 'color': '#88CCEE', 'radius': 5}

    '''
    Return the estimated type of a given decoded item.

    :param sha1_string: sha1_string
    '''
    def get_mimetype(self):
        return r_objects.hget(f'meta:{self.type}:{self.id}', 'mime')

    def set_mimetype(self, mimetype):
        return r_objects.hset(f'meta:{self.type}:{self.id}', 'mime', mimetype)

    def get_size(self):
        return r_objects.hget(f'meta:{self.type}:{self.id}', 'size')

    def set_size(self, size):
        return r_objects.hset(f'meta:{self.type}:{self.id}', 'size', int(size))

    def get_rel_path(self, mimetype=None):
        if not mimetype:
            mimetype = self.get_mimetype()
        return os.path.join(HASH_DIR, mimetype, self.id[0:2], self.id)

    def get_filepath(self, mimetype=None):
        return os.path.join(os.environ['AIL_HOME'], self.get_rel_path(mimetype=mimetype))

    def get_content(self, mimetype=None):
        filepath = self.get_filepath(mimetype=mimetype)
        with open(filepath, 'rb') as f:
            file_content = BytesIO(f.read())
        return file_content

    def get_zip_content(self):
        # mimetype = self.get_estimated_type()
        zip_content = BytesIO()
        with zipfile.ZipFile(zip_content, "w") as zf:
            # TODO: Fix password
            # zf.setpassword(b"infected")
            zf.writestr(self.id, self.get_content().getvalue())
        zip_content.seek(0)
        return zip_content

    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('file')
        obj.first_seen = self.get_first_seen()
        obj.last_seen = self.get_last_seen()

        obj_attrs.append(obj.add_attribute('sha1', value=self.id))
        obj_attrs.append(obj.add_attribute('mimetype', value=self.get_mimetype()))
        obj_attrs.append(obj.add_attribute('malware-sample', value=self.id, data=self.get_content()))
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    ############################################################################
    ############################################################################
    ############################################################################

    def get_decoders(self):
        return ['base64', 'binary', 'hexadecimal']

    def get_meta(self, options=set()):
        meta = self._get_meta(options=options)
        meta['id'] = self.id
        if 'mimetype' in options:
            meta['mimetype'] = self.get_mimetype()
        if 'icon' in options:
            if 'mimetype' in meta:
                mimetype = meta['mimetype']
            else:
                mimetype = None
            meta['icon'] = self.get_svg_icon(mimetype=mimetype)
        if 'size' in options:
            meta['size'] = self.get_size()
        if 'tags' in options:
            meta['tags'] = self.get_tags()
        if 'vt' in options:
            meta['vt'] = self.get_meta_vt()
        return meta

    def get_meta_vt(self):
        link = r_objects.hget(f'meta:{self.type}:{self.id}', 'vt_link')
        report = r_objects.hget(f'meta:{self.type}:{self.id}', 'vt_report')
        if link or report:
            return {'link': link, 'report': report}
        else:
            return {}

    # TODO
    def guess_mimetype(self, bytes_content):
        # if not bytes_content:
        #     bytes_content = self.get_content()
        return magic.from_buffer(bytes_content, mime=True)

    # avoid counting the same hash multiple time on the same item
    #       except if different encoding

    def is_seen_this_day(self, date):
        return bool(self.get_nb_seen_by_date(Date.get_today_date_str()))

    def save_file(self, b_content, mimetype): # TODO TEST ME
        filepath = self.get_filepath(mimetype=mimetype)
        if os.path.isfile(filepath):
            # print('File already exist')
            return False
        # create dir
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filepath, 'wb') as f:
            f.write(b_content)

        # create meta
        self._add_create()
        self.set_mimetype(mimetype)
        self.set_size(os.path.getsize(filepath))

        return True

    def add(self, algo_name, date, obj_id, mimetype=None):
        self._add(date, obj_id)
        if not mimetype:
            mimetype = self.get_mimetype()

        is_new_decoded = r_objects.sadd(f'decoded:algo:{algo_name}:{date}', self.id)  # filter by algo + sparkline
        # uniq decoded in this algo today
        if int(is_new_decoded):
            r_objects.zincrby(f'decoded:algos:{date}', 1, algo_name)  # pie chart

        # mimetype -> decodeds
        is_new_decoded = r_objects.sadd(f'decoded:mime:{mimetype}:{date}', self.id)  # filter by mimetype
        # uniq decoded in this mimetype today
        if int(is_new_decoded):
            r_objects.zincrby(f'decoded:mime:{date}', 1, mimetype)  # TDO ADD OPTION TO CALC IF NOT EXISTS
            r_objects.sadd('decoded:mimetypes', mimetype)

        # algo + mimetype -> Decodeds
        # -> sinter with r_objects.sunion(f'decoded:algo:{algo_name}:{date}')

    # # TODO: ADD items
    # def create(self, content, date, mimetype=None):
    #     if not mimetype:
    #         mimetype = self.guess_mimetype(content)
    #     self.save_file(content, mimetype)
    #
    #
    #     update_decoded_daterange(sha1_string, date_from)
    #     if date_from != date_to and date_to:
    #         update_decoded_daterange(sha1_string, date_to)

        #######################################################################################
        #######################################################################################

    def is_vt_enabled(self):
        return VT_ENABLED

    def set_vt_report(self, report):
        r_objects.hset(f'meta:{self.type}:{self.id}', 'vt_report', report)

    def set_meta_vt(self, link, report):
        r_objects.hset(f'meta:{self.type}:{self.id}', 'vt_link', link)
        self.set_vt_report(report)

    def refresh_vt_report(self):
        params = {'apikey': VT_TOKEN, 'resource': self.id}
        response = requests.get('https://www.virustotal.com/vtapi/v2/file/report', params=params)
        if response.status_code == 200:
            json_response = response.json()
            response_code = json_response['response_code']
            # report exist
            if response_code == 1:
                total = json_response['total']
                detection = json_response['positives']
                report = f'Detection {detection}/{total}'
            # no report found
            elif response_code == 0:
                report = 'No report found'
            # file in queue
            elif response_code == -2:
                report = 'In Queue - Refresh'
            else:
                report = 'Error - Unknown VT response'
            self.set_vt_report(report)
            print(json_response)
            print(response_code)
            print(report)
            return report
        elif response.status_code == 403:
            return 'Virustotal key is incorrect (e.g. for public API not for virustotal intelligence), authentication failed'
        elif response.status_code == 204:
            return 'Rate Limited'

    def send_to_vt(self):
        files = {'file': (self.id, self.get_content())}
        response = requests.post('https://www.virustotal.com/vtapi/v2/file/scan', files=files, params= {'apikey': VT_TOKEN})
        json_response = response.json()
        link = json_response['permalink'].split('analysis')[0] + 'analysis/'
        self.set_meta_vt(link, 'Please Refresh')

############################################################################

def is_vt_enabled():
    return VT_ENABLED

def get_all_decodeds():
    return r_objects.smembers(f'decoded:all')

def get_algos():
    return ['base64', 'binary', 'hexadecimal']

def get_all_mimetypes():
    return r_objects.smembers('decoded:mimetypes')

def get_nb_decodeds_by_date(date):
    return r_objects.zcard(f'decoded:date:{date}')

def get_decodeds_by_date(date):
    return r_objects.zrange(f'decoded:date:{date}', 0, -1)

def get_algo_decodeds_by_date(date, algo):
    return r_objects.smembers(f'decoded:algo:{algo}:{date}')

def get_mimetype_decodeds_by_date(date, mimetype):
    return r_objects.smembers(f'decoded:mime:{mimetype}:{date}')

def get_algo_mimetype_decodeds_by_date(date, algo, mimetype):
    return r_objects.sinter(f'decoded:algo:{algo}:{date}', f'decoded:mime:{mimetype}:{date}')

def get_decodeds_by_daterange(date_from, date_to, algo=None, mimetype=None):
    decodeds = set()
    if not algo and not mimetype:
        for date in Date.substract_date(date_from, date_to):
            decodeds = decodeds | set(get_decodeds_by_date(date))
    elif algo and not mimetype:
        for date in Date.substract_date(date_from, date_to):
            decodeds = decodeds | get_algo_decodeds_by_date(date, algo)
    elif mimetype and not algo:
        for date in Date.substract_date(date_from, date_to):
            decodeds = decodeds | get_mimetype_decodeds_by_date(date, mimetype)
    elif algo and mimetype:
        for date in Date.substract_date(date_from, date_to):
            decodeds = decodeds | get_algo_mimetype_decodeds_by_date(date, algo, mimetype)
    return decodeds

def sanitise_algo(algo):
    if algo in get_algos():
        return algo
    else:
        return None

def sanitise_mimetype(mimetype):
    if mimetype:
        if r_objects.sismember('decoded:mimetypes', mimetype):
            return mimetype
        else:
            return None

############################################################################

def sanityze_decoder_names(decoder_name):
    if decoder_name not in Decodeds.get_algos():
        return None
    else:
        return decoder_name

def sanityze_mimetype(mimetype):
    if mimetype == 'All types':
        return None
    elif not r_objects.sismember(f'decoded:mimetypes', mimetype):
        return None
    else:
        return mimetype

# TODO
def pie_chart_mimetype_json(date_from, date_to, mimetype, decoder_name):
    if mimetype:
        all_mimetypes = [mimetype]
    else:
        all_mimetypes = get_all_mimetypes()
    date_range = Date.substract_date(date_from, date_to)
    for date in date_range:
        for mimet in all_mimetypes:
            pass

# TODO
def pie_chart_decoder_json(date_from, date_to, mimetype):
    all_algos = get_algos()
    date_range = Date.substract_date(date_from, date_to)
    if not date_range:
        date_range.append(Date.get_today_date_str())
    nb_algos = {}
    for date in date_range:
        for algo_name in all_algos:
            # if not mimetype:
            nb = r_objects.zscore(f'decoded:algos:{date}', algo_name)
            # TODO mimetype necoding per day
            # else:
            #     nb = r_metadata.zscore(f'{algo_name}_type:{mimetype}', date)
            if nb is None:
                nb = 0
            else:
                nb = int(nb)
            nb_algos[algo_name] = nb_algos.get(algo_name, 0) + nb
    pie_chart = []
    for algo_name in all_algos:
        pie_chart.append({'name': algo_name, 'value': nb_algos[algo_name]})
    return pie_chart

# TODO FILTER BY ALGO
def pie_chart_mimetype_json(date_from, date_to, algo):
    date_range = Date.substract_date(date_from, date_to)
    if not date_range:
        date_range.append(Date.get_today_date_str())
    mimetypes = {}
    if len(date_range) == 1:
        mimes = r_objects.zrange(f'decoded:mime:{date_range[0]}', 0, -1, withscores=True)
        for t_mime in mimes:
            mime, nb = t_mime
            mimetypes[mime] = int(nb)
    else:
        mimetypes = {}
        for date in date_range:
            mimes = r_objects.zrange(f'decoded:mime:{date}', 0, -1, withscores=True)
            for t_mime in mimes:
                mime, nb = t_mime
                mimetypes[mime] = mimetypes.get(mime, 0) + int(nb)
    top5_mimes = sorted(mimetypes, key=mimetypes.get, reverse=True)[:5]
    pie_chart = []
    for mime in top5_mimes:
        pie_chart.append({'name': mime, 'value': mimetypes[mime]})
    return pie_chart

def barchart_range_json(date_from, date_to, mimetype=None):
    date_range = Date.substract_date(date_from, date_to)
    if not date_range:
        date_range.append(Date.get_today_date_str())
    barchart = []
    if mimetype:
        for date in date_range:
            range_day = {'date': f'{date[0:4]}-{date[4:6]}-{date[6:8]}'}
            nb_day = r_objects.scard(f'decoded:mime:{mimetype}:{date}')
            range_day[mimetype] = nb_day
            barchart.append(range_day)
    else:
        # algo by mimetype, date = mimetype
        if len(date_range) == 1:
            mimes = r_objects.zrange(f'decoded:mime:{date_range[0]}', 0, -1, withscores=True)
            # TODO
            # UNION
            # f'decoded:algo:{algo_name}:{date}'
            # f'decoded:mime:{mimetype}:{date}'
            for t_mime in mimes:
                mime, nb = t_mime
                range_day = {'date': mime, 'mimetype': nb}
                barchart.append(range_day)
        # mimetypes by date
        else:
            mimetypes = set()
            for date in date_range:
                range_day = {'date': f'{date[0:4]}-{date[4:6]}-{date[6:8]}'}
                mimes = r_objects.zrange(f'decoded:mime:{date}', 0, -1, withscores=True)
                for t_mime in mimes:
                    mime, nb = t_mime
                    mimetypes.add(mime)
                    range_day[mime] = int(nb)
                barchart.append(range_day)
            if not mimetypes:
                mimetypes.add('No Data')
            for row in barchart:
                for mime in mimetypes:
                    if mime not in row:
                        row[mime] = 0
    return barchart

def graphline_json(decoded_id):
    decoded = Decoded(decoded_id)
    graphline = []
    if decoded.exists():
        nb_day = 30
        for date in Date.get_previous_date_list(nb_day):
            graphline.append({'date': f'{date[0:4]}-{date[4:6]}-{date[6:8]}', 'value': decoded.get_nb_seen_by_date(date)})
    return graphline

def api_pie_chart_decoder_json(date_from, date_to, mimetype):
    mimetype = sanityze_mimetype(mimetype)
    date = Date.sanitise_date_range(date_from, date_to)
    return pie_chart_decoder_json(date['date_from'], date['date_to'], mimetype)

def api_pie_chart_mimetype_json(date_from, date_to, algo):
    algo = sanitise_algo(algo)
    date = Date.sanitise_date_range(date_from, date_to)
    return pie_chart_mimetype_json(date['date_from'], date['date_to'], algo)

def api_barchart_range_json(date_from, date_to, mimetype):
    date = Date.sanitise_date_range(date_from, date_to)
    if mimetype:
        mimetype = sanityze_mimetype(mimetype)
    return barchart_range_json(date['date_from'], date['date_to'], mimetype=mimetype)

def _delete_old_json_descriptor():
    decodeds = []
    hash_dir = os.path.join(os.environ['AIL_HOME'], HASH_DIR)
    for root, dirs, files in os.walk(hash_dir):
        for file in files:
            if file.endswith('.json'):
                decoded_path = f'{root}/{file}'
                os.remove(decoded_path)
    return decodeds


# TODO
def get_all_decodeds_files():
    decodeds = []
    hash_dir = os.path.join(os.environ['AIL_HOME'], HASH_DIR)
    if not hash_dir.endswith("/"):
        hash_dir = f"{hash_dir}/"
    for root, dirs, files in os.walk(hash_dir):
        for file in files:
            # decoded_path = f'{root}{file}'
            decodeds.append(file)
    return decodeds

# if __name__ == '__main__':

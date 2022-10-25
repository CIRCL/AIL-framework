#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import requests
import zipfile

from flask import url_for
from io import BytesIO

sys.path.append(os.environ['AIL_BIN'])
from lib.ConfigLoader import ConfigLoader
from lib.objects.abstract_object import AbstractObject
from lib.item_basic import is_crawled, get_item_domain

from packages import Date

sys.path.append('../../configs/keys')
try:
    from virusTotalKEYS import vt_key
    if vt_key != '':
        VT_TOKEN = vt_key
        VT_ENABLED = True
        #print('VT submission is enabled')
    else:
        VT_ENABLED = False
        #print('VT submission is disabled')
except:
    VT_TOKEN = None
    VT_ENABLED = False
    #print('VT submission is disabled')

config_loader = ConfigLoader()
r_metadata = config_loader.get_db_conn("Kvrocks_Objects")

r_metadata = config_loader.get_redis_conn("ARDB_Metadata")
HASH_DIR = config_loader.get_config_str('Directories', 'hash')
baseurl = config_loader.get_config_str("Notifications", "ail_domain")
config_loader = None


################################################################################
################################################################################
################################################################################

# # TODO: COMPLETE CLASS

class Decoded(AbstractObject):
    """
    AIL Decoded Object. (strings)
    """

    def __init__(self, id):
        super(Decoded, self).__init__('decoded', id)

    def exists(self):
        return r_metadata.exists(f'metadata_hash:{self.id}')

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

    def get_svg_icon(self):
        file_type = self.get_estimated_type()
        file_type = file_type.split('/')[0]
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
        return {'style': 'fas', 'icon': icon, 'color': '#88CCEE', 'radius':5}

    '''
    Return the estimated type of a given decoded item.

    :param sha1_string: sha1_string
    '''
    def get_estimated_type(self):
        return r_metadata.hget(f'metadata_hash:{self.id}', 'estimated_type')

    def get_rel_path(self, mimetype=None):
        if not mimetype:
            mimetype = self.get_estimated_type()
        return os.path.join(HASH_DIR, mimetype, self.id[0:2], self.id)

    def get_filepath(self, mimetype=None):
        return os.path.join(os.environ['AIL_HOME'], self.get_rel_path(mimetype=mimetype))

    def get_content(self, mimetype=None):
        filepath = self.get_filepath(mimetype=mimetype)
        with open(filepath, 'rb') as f:
            file_content = BytesIO(f.read())
        return file_content

    def get_zip_content(self):
        mimetype = self.get_estimated_type()
        zip_content = BytesIO()
        with zipfile.ZipFile(zip_content, "w") as zf:
            # TODO: Fix password
            #zf.setpassword(b"infected")
            zf.writestr( self.id, self.get_content().getvalue())
        zip_content.seek(0)
        return zip_content


    def get_misp_object(self):
        obj_attrs = []
        obj = MISPObject('file')
        obj.first_seen = self.get_first_seen()
        obj.last_seen = self.get_last_seen()

        obj_attrs.append( obj.add_attribute('sha1', value=self.id) )
        obj_attrs.append( obj.add_attribute('mimetype', value=self.get_estimated_type()) )
        obj_attrs.append( obj.add_attribute('malware-sample', value=self.id, data=self.get_content()) )
        for obj_attr in obj_attrs:
            for tag in self.get_tags():
                obj_attr.add_tag(tag)
        return obj

    ############################################################################
    ############################################################################
    ############################################################################
    def get_decoders(self):
        return ['base64', 'binary', 'hexadecimal']

    def get_first_seen(self):
        res = r_metadata.hget(f'metadata_hash:{self.id}', 'first_seen')
        if res:
            return int(res)
        else:
            return 99999999

    def get_last_seen(self):
        res = r_metadata.hget(f'metadata_hash:{self.id}', 'last_seen')
        if res:
            return int(res)
        else:
            return 0

    def set_first_seen(self, date):
        r_metadata.hset(f'metadata_hash:{self.id}', 'first_seen', date)

    def set_last_seen(self, date):
        r_metadata.hset(f'metadata_hash:{self.id}', 'last_seen', date)

    def update_daterange(self, date):
        first_seen = self.get_first_seen()
        last_seen = self.get_last_seen()
        if date < first_seen:
            self.set_first_seen(date)
        if date > last_seen:
            self.set_last_seen(date)

    def get_meta(self, options=set()):
        meta = {'id': self.id,
                'subtype': self.subtype,
                'tags': self.get_tags()}
        return meta

    def get_meta_vt(self):
        meta = {}
        meta['link'] = r_metadata.hget(f'metadata_hash:{self.id}', 'vt_link')
        meta['report'] = r_metadata.hget(f'metadata_hash:{self.id}', 'vt_report')
        return meta

    def guess_mimetype(self, bytes_content):
        return magic.from_buffer(bytes_content, mime=True)

    def _save_meta(self, filepath, mimetype):
        # create hash metadata
        r_metadata.hset(f'metadata_hash:{self.id}', 'size', os.path.getsize(filepath))
        r_metadata.hset(f'metadata_hash:{self.id}', 'estimated_type', mimetype)
        r_metadata.sadd('hash_all_type', mimetype) #################################################### rename ????

    def save_file(self, content, mimetype): #####################################################
        filepath = self.get_filepath(mimetype=mimetype)
        if os.path.isfile(filepath):
            #print('File already exist')
            return False
        # create dir
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filepath, 'wb') as f:
            f.write(file_content)

        # create hash metadata
        self._save_meta(filepath, mimetype)
        return True

    # avoid counting the same hash multiple time on the same item
    #       except if defferent encoding

    def is_seen_this_day(self, date):
        for decoder in get_decoders_names():
            if r_metadata.zscore(f'{decoder}_date:{date}', self.id):
                return True
        return False

    def add(self, decoder_name, date, obj_id, mimetype):

        if not self.is_seen_this_day(date):
            # mimetype
            r_metadata.zincrby(f'decoded:mimetype:{date}', mimetype, 1)
            r_metadata.sadd(f'decoded:mimetypes', mimetype)

        # filter hash encoded in the same object
        if not self.is_correlated('item', None, obj_id):

            r_metadata.hincrby(f'metadata_hash:{self.id}', f'{decoder_name}_decoder', 1)
            r_metadata.zincrby(f'{decoder_name}_type:{mimetype}', date, 1)

            r_metadata.incrby(f'{decoder_name}_decoded:{date}', 1)
            r_metadata.zincrby(f'{decoder_name}_date:{date}', self.id, 1)


            self.update_daterange(date)

        # First Hash for this decoder this day







            # Correlations
            self.add_correlation('item', '', obj_id)
            # domain
            if is_crawled(obj_id):
                domain = get_item_domain(obj_id)
                self.add_correlation('domain', '', domain)


        # Filter duplicates ######################################################################
        # Filter on item + hash for this day

        # filter Obj Duplicate

        # first time we see this day
        # iterate on all decoder




        ######################################################################

        # first time we see this hash today


        # mimetype # # # # # # # #
        r_metadata.zincrby(f'decoded:mimetype:{date}', mimetype, 1)

        # create hash metadata
        r_metadata.sadd(f'decoded:mimetypes', mimetype)



    # # TODO: DUPLICATES + check fields
    def add(self, decoder_name, date, obj_id, mimetype):
        self.update_daterange(date)

        r_metadata.incrby(f'{decoder_type}_decoded:{date}', 1)
        r_metadata.zincrby(f'{decoder_type}_date:{date}', self.id, 1)

        r_metadata.hincrby(f'metadata_hash:{self.id}', f'{decoder_type}_decoder', 1)
        r_metadata.zincrby(f'{decoder_type}_type:{mimetype}', date, 1) # # TODO: # DUP1

        ################################################################ # TODO:  REMOVE ?????????????????????????????????
        r_metadata.zincrby(f'{decoder_type}_hash:{self.id}', obj_id, 1) # number of b64 on this item


        # first time we see this hash encoding on this item
        if not r_metadata.zscore(f'{decoder_type}_hash:{self.id}', obj_id):

            # create hash metadata
            r_metadata.sadd(f'hash_{decoder_type}_all_type', mimetype)

            # first time we see this hash encoding today
            if not r_metadata.zscore(f'{decoder_type}_date:{date}', self.id):
                r_metadata.zincrby(f'{decoder_type}_type:{mimetype}', date, 1) # # TODO: # DUP1


        # Correlations
        self.add_correlation('item', '', obj_id)
        # domain
        if is_crawled(obj_id):
            domain = get_item_domain(obj_id)
            self.add_correlation('domain', '', domain)


    # NB of MIMETYPE / DAY -> ALL HASH OR UNIQ HASH ??????

    # # TODO: ADD items
    def create(self, content, date, mimetype=None):
        if not mimetype:
            mimetype = self.guess_mimetype(content)
        self.save_file(content, mimetype)


        update_decoded_daterange(sha1_string, date_from)
        if date_from != date_to and date_to:
            update_decoded_daterange(sha1_string, date_to)

        #######################################################################################
        #######################################################################################

        #######################################################################################
        #######################################################################################

    def is_vt_enabled(self):
        return VT_ENABLED

    def set_vt_report(self, report):
        r_metadata.hset(f'metadata_hash:{self.id}', 'vt_report', report)

    def set_meta_vt(self, link, report):
        r_metadata.hset(f'metadata_hash:{self.id}', 'vt_link', link)
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
    ############################################################################

def get_decoders_names():
    return ['base64', 'binary', 'hexadecimal']

def get_all_mimetypes():
    return r_metadata.smembers(f'decoded:mimetypes')

def sanityze_decoder_names(decoder_name):
    if decoder_name not in Decodeds.get_decoders_names():
        return None
    else:
        return decoder_name

def sanityze_mimetype(mimetype):
    if mimetype == 'All types':
        return None
    elif not r_metadata.sismember('hash_all_type', mimetype):
        return None
    else:
        return mimetype

def pie_chart_mimetype_json(date_from, date_to, mimetype, decoder_name):
    if mimetype:
        all_mimetypes = [mimetype]
    else:
        all_mimetypes = get_all_mimetypes()
    date_range = Date.substract_date(date_from, date_to)
    for date in date_range:
        for mimet in all_mimetypes:
            pass

def pie_chart_decoder_json(date_from, date_to, mimetype):
    all_decoder = get_decoders_names()
    date_range = Date.substract_date(date_from, date_to)
    if not date_range:
        date_range.append(Date.get_today_date_str())
    nb_decoder = {}
    for date in date_range:
        for decoder_name in all_decoder:
            if not mimetype:
                nb = r_metadata.get(f'{decoder_name}_decoded:{date}')
                if nb is None:
                    nb = 0
                else:
                    nb = int(nb)
            else:
                nb = r_metadata.zscore(f'{decoder_name}_type:{mimetype}', date)
            nb_decoder[decoder_name] = nb_decoder.get(decoder_name, 0) + nb
    pie_chart = []
    for decoder_name in all_decoder:
        pie_chart.append({'name': decoder_name, 'value': nb_decoder[decoder_name]})
    return pie_chart

def api_pie_chart_decoder_json(date_from, date_to, mimetype):
    mimetype = sanityze_mimetype(mimetype)
    date = Date.sanitise_date_range(date_from, date_to)
    return pie_chart_decoder_json(date['date_from'], date['date_to'], mimetype)

def _delete_old_json_descriptor():
    decodeds = []
    hash_dir = os.path.join(os.environ['AIL_HOME'], HASH_DIR)
    for root, dirs, files in os.walk(hash_dir):
        for file in files:
            if file.endswith('.json'):
                decoded_path = f'{root}/{file}'
                os.remove(decoded_path)
    return decodeds

def get_all_decodeds():
    decodeds = []
    hash_dir = os.path.join(os.environ['AIL_HOME'], HASH_DIR)
    if not hash_dir.endswith("/"):
        hash_dir = f"{hash_dir}/"
    for root, dirs, files in os.walk(hash_dir):
        for file in files:
            decoded_path = f'{root}{file}'
            decodeds.append(file)
    return decodeds

 #if __name__ == '__main__':

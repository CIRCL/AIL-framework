#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import html2text

import gcld3
from lexilang.detector import detect as lexilang_detect
from libretranslatepy import LibreTranslateAPI

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader
from lib.ail_core import get_object_all_subtypes

config_loader = ConfigLoader()
r_cache = config_loader.get_redis_conn("Redis_Cache")
r_lang = config_loader.get_db_conn("Kvrocks_Languages")
TRANSLATOR_URL = config_loader.get_config_str('Translation', 'libretranslate')
config_loader = None


dict_iso_languages = {
    'afr': 'Afrikaans',
    'amh': 'Amharic',
    'ara': 'Arabic',
    'aze': 'Azerbaijani',
    'ben': 'Bengali',
    'bos': 'Bosnian',
    'bul': 'Bulgarian',
    'cat': 'Catalan',
    'ceb': 'Cebuano',
    'ces': 'Czech',
    'cos': 'Corsican',
    'cym': 'Welsh',
    'dan': 'Danish',
    'deu': 'German',
    'ell': 'Greek',
    'eng': 'English',
    'epo': 'Esperanto',
    'est': 'Estonian',
    'eus': 'Basque',
    'fas': 'Persian',
    'fin': 'Finnish',
    'fil': 'Filipino',
    'fra': 'French',
    'fry': 'Western Frisian',
    'gla': 'Scottish Gaelic',
    'gle': 'Irish',
    'glg': 'Galician',
    'guj': 'Gujarati',
    'hat': 'Haitian',
    'hau': 'Hausa',
    'haw': 'Hawaiian',
    'hbs': 'Serbo-Croatian',
    'heb': 'Hebrew',
    'hin': 'Hindi',
    'hmn': 'Hmong',
    'hrv': 'Croatian',
    'hun': 'Hungarian',
    'hye': 'Armenian',
    'ibo': 'Igbo',
    'ind': 'Indonesian',
    'isl': 'Icelandic',
    'ita': 'Italian',
    'jav': 'Javanese',
    'jpn': 'Japanese',
    'kab': 'Kabyle',
    'kan': 'Kannada',
    'kat': 'Georgian',
    'kaz': 'Kazakh',
    'khm': 'Khmer',
    'kir': 'Kirghiz',
    'kor': 'Korean',
    'kur': 'Kurdish',
    'lao': 'Lao',
    'lat': 'Latin',
    'lav': 'Latvian',
    'lit': 'Lithuanian',
    'ltz': 'Luxembourgish',
    'mal': 'Malayalam',
    'mar': 'Marathi',
    'mkd': 'Macedonian',
    'mlg': 'Malagasy',
    'mlt': 'Maltese',
    'mon': 'Mongolian',
    'mri': 'Maori',
    'msa': 'Malay',
    'mya': 'Burmese',
    'nep': 'Nepali',
    'nld': 'Dutch',
    'nor': 'Norwegian',
    'nya': 'Nyanja',
    'oci': 'Occitan',
    'pan': 'Panjabi',
    'pol': 'Polish',
    'por': 'Portuguese',
    'pus': 'Pushto',
    'ron': 'Romanian',
    'rus': 'Russian',
    'sin': 'Sinhala',
    'slk': 'Slovak',
    'slv': 'Slovenian',
    'smo': 'Samoan',
    'sna': 'Shona',
    'snd': 'Sindhi',
    'som': 'Somali',
    'sot': 'Southern Sotho',
    'spa': 'Spanish',
    'sqi': 'Albanian',
    'sun': 'Sundanese',
    'swa': 'Swahili',
    'swe': 'Swedish',
    'tam': 'Tamil',
    'tel': 'Telugu',
    'tgk': 'Tajik',
    'tgl': 'Tagalog',
    'tha': 'Thai',
    'tur': 'Turkish',
    'ukr': 'Ukrainian',
    'urd': 'Urdu',
    'uzb': 'Uzbek',
    'vie': 'Vietnamese',
    'xho': 'Xhosa',
    'yid': 'Yiddish',
    'yor': 'Yoruba',
    'zho': 'Chinese',
    'zul': 'Zulu'
}

def create_dict_iso_languages():
    dict_lang = {}
    for code in dict_iso_languages:
        dict_lang[dict_iso_languages[code]] = code
    return dict_lang


dict_languages_iso = create_dict_iso_languages()

dict_iso_1_to_3 = {
    'af': 'afr',
    'am': 'amh',
    'ar': 'ara',
    'az': 'aze',
    'bg': 'bul',
    'bn': 'ben',
    'bs': 'bos',
    'ca': 'cat',
    'co': 'cos',
    'cs': 'ces',
    'cy': 'cym',
    'da': 'dan',
    'de': 'deu',
    'el': 'ell',
    'en': 'eng',
    'eo': 'epo',
    'es': 'spa',
    'et': 'est',
    'eu': 'eus',
    'fa': 'fas',
    'fi': 'fin',
    'fr': 'fra',
    'fy': 'fry',
    'ga': 'gle',
    'gd': 'gla',
    'gl': 'glg',
    'gu': 'guj',
    'ha': 'hau',
    'he': 'heb',
    'hi': 'hin',
    'hr': 'hrv',
    'ht': 'hat',
    'hu': 'hun',
    'hy': 'hye',
    'id': 'ind',
    'ig': 'ibo',
    'is': 'isl',
    'it': 'ita',
    'ja': 'jpn',
    'jv': 'jav',
    'ka': 'kat',
    'kk': 'kaz',
    'km': 'khm',
    'kn': 'kan',
    'ko': 'kor',
    'ku': 'kur',
    'ky': 'kir',
    'la': 'lat',
    'lb': 'ltz',
    'lo': 'lao',
    'lt': 'lit',
    'lv': 'lav',
    'mg': 'mlg',
    'mi': 'mri',
    'mk': 'mkd',
    'ml': 'mal',
    'mn': 'mon',
    'mr': 'mar',
    'ms': 'msa',
    'mt': 'mlt',
    'my': 'mya',
    'ne': 'nep',
    'nl': 'nld',
    'no': 'nor',
    'nb': 'nor', # libretranslate incorrect mapping ?
    'ny': 'nya',
    'pa': 'pan',
    'pl': 'pol',
    'ps': 'pus',
    'pt': 'por',
    'ro': 'ron',
    'ru': 'rus',
    'sd': 'snd',
    'si': 'sin',
    'sk': 'slk',
    'sl': 'slv',
    'sm': 'smo',
    'sn': 'sna',
    'so': 'som',
    'sq': 'sqi',
    'sr': 'hbs',  # lexilang invalid use of sr. Should se deprecated sh
    'st': 'sot',
    'su': 'sun',
    'sv': 'swe',
    'sw': 'swa',
    'ta': 'tam',
    'te': 'tel',
    'tg': 'tgk',
    'th': 'tha',
    'tl': 'tgl',
    'tr': 'tur',
    'uk': 'ukr',
    'ur': 'urd',
    'uz': 'uzb',
    'vi': 'vie',
    'xh': 'xho',
    'yi': 'yid',
    'yo': 'yor',
    'zh': 'zho',  # {'iso': 'zt', 'language': 'Chinese (traditional)'} libretranslate INVALID code
    'zu': 'zul'
}

def convert_iso_code(code_iso1):
    iso3 = dict_iso_1_to_3.get(code_iso1)
    if iso3:
        return iso3
    elif len(code_iso1) == 3:
        return code_iso1

def get_language_from_iso(iso_language):
    return dict_iso_languages.get(iso_language, None)

def get_languages_from_iso(l_iso_languages, sort=False):
    l_languages = []
    for iso_language in l_iso_languages:
        language = get_language_from_iso(iso_language)
        if language:
            l_languages.append(language)
    if sort:
        l_languages = sorted(l_languages)
    return l_languages

def get_iso_from_language(language):
    return dict_languages_iso.get(language, None)

def get_iso_from_languages(l_languages, sort=False):
    l_iso = []
    for language in l_languages:
        iso_lang = get_iso_from_language(language)
        if iso_lang:
            l_iso.append(iso_lang)
    if sort:
        l_iso = sorted(l_iso)
    return l_iso


def get_translator_instance():
    return TRANSLATOR_URL

def _get_html2text(content, ignore_links=False):
    h = html2text.HTML2Text()
    h.ignore_links = ignore_links
    h.ignore_images = ignore_links
    content = h.handle(content)
    if content == '\n\n':
        content = ''
    return content

def _clean_text_to_translate(content, html=False, keys_blocks=True):
    if html:
        content = _get_html2text(content, ignore_links=True)

    # REMOVE URLS
    regex = r'\b(?:http://|https://)?(?:[a-zA-Z\d-]{,63}(?:\.[a-zA-Z\d-]{,63})+)(?:\:[0-9]+)*(?:/(?:$|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*\b'
    url_regex = re.compile(regex)
    urls = url_regex.findall(content)
    urls = sorted(urls, key=len, reverse=True)
    for url in urls:
        content = content.replace(url, '')

    # REMOVE PGP Blocks
    if keys_blocks:
        regex_pgp_public_blocs = r'-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]+?-----END PGP PUBLIC KEY BLOCK-----'
        regex_pgp_signature = r'-----BEGIN PGP SIGNATURE-----[\s\S]+?-----END PGP SIGNATURE-----'
        regex_pgp_message = r'-----BEGIN PGP MESSAGE-----[\s\S]+?-----END PGP MESSAGE-----'
        re.compile(regex_pgp_public_blocs)
        re.compile(regex_pgp_signature)
        re.compile(regex_pgp_message)
        res = re.findall(regex_pgp_public_blocs, content)
        for it in res:
            content = content.replace(it, '')
        res = re.findall(regex_pgp_signature, content)
        for it in res:
            content = content.replace(it, '')
        res = re.findall(regex_pgp_message, content)
        for it in res:
            content = content.replace(it, '')
    return content

#### LANGUAGE ENGINE ####

# first seen
# last seen
# language by date -> iter on object date ????

## Langs
def get_language_obj_types(language):
    return r_lang.smembers(f'languages:{language}')

def get_language_objs(language, obj_type, obj_subtype=''):
    return r_lang.smembers(f'langs:{obj_type}:{obj_subtype}:{language}')

# def get_languages_objs(languages, obj_type, obj_subtype='')

## Objs
def get_objs_languages(obj_type, obj_subtype=''):
    if obj_subtype is None:
        obj_subtype = ''
    return r_lang.smembers(f'objs:lang:{obj_type}:{obj_subtype}')

## Obj
def get_obj_languages(obj_type, obj_subtype, obj_id):
    return r_lang.smembers(f'obj:lang:{obj_type}:{obj_subtype}:{obj_id}')

def get_obj_languages_objs_by_lang(obj_type, obj_subtype, obj_id, lang):
    return r_lang.smembers(f'obj:lang:{lang}:{obj_type}:{obj_subtype}:{obj_id}')

def get_obj_language_stats(obj_type, obj_subtype, obj_id):
    return r_lang.zrange(f'obj:langs:stat:{obj_type}:{obj_subtype}:{obj_id}', 0, -1, withscores=True)

def get_obj_main_language(obj_type, obj_subtype, obj_id):
    language = r_lang.zrevrange(f'obj:langs:stat:{obj_type}:{obj_subtype}:{obj_id}', 0, 0)
    if language:
        return language[0]

# obj_type -> languages
# obj_type + subtype -> languages   - chat:telegram, subchannel:telegram, thread:telegram, user-account:telegram
#
# Stats ZSET obj_type + subtype -> languages
#
# obj -> languages
#
# if containers: (user-account as container)
#   container: ZSET -> languages
#   container + language -> objs_global_id
# else:
#   obj_type + subtype + language -> obj_global_id

def get_container_language_objs(language, global_id):
    return r_lang.smembers(f'obj:lang:{language}:{global_id}')  # TODO REPLACE ME obj->cobj

def _add_container_language(language, global_id, obj_gid):
    r_lang.sadd(f'obj:lang:{language}:{global_id}', obj_gid)
    nb = r_lang.zincrby(f'obj:langs:stat:{global_id}', 1, language)
    if int(nb) == 1:
        c_type, c_subtype, _ = global_id.split(':', 2)
        r_lang.zincrby(f'container:stat:{c_type}:{c_subtype}', 1, language)

def _delete_container_language(language, global_id, obj_gid):
    r_lang.srem(f'obj:lang:{language}:{global_id}', obj_gid)
    r = r_lang.zincrby(f'obj:langs:stat:{global_id}', -1, language)
    if int(r) < 1:
        r_lang.zrem(f'obj:langs:stat:{global_id}', language)
        c_type, c_subtype, _ = global_id.split(':', 2)
        nb = r_lang.zincrby(f'container:stat:{c_type}:{c_subtype}', -1, language)
        if int(nb) < 1:
            r_lang.zrem(f'container:stat:{c_type}:{c_subtype}', language)
            return True
        return False
    return False

def _delete_obj_type_stats(language, obj_type, obj_subtype):
    delete_lang_type = True
    for obj_type in get_object_all_subtypes(obj_type):
        if r_lang.sismember(f'objs:lang:{obj_type}:{obj_subtype}', language):
            delete_lang_type = False
            break
    if delete_lang_type:
        r_lang.srem(f'objs:langs:{obj_type}', language)

def add_obj_language(language, obj_type, obj_subtype, obj_id, objs_containers=set()):  # (s)
    if not obj_subtype:
        obj_subtype = ''
    obj_global_id = f'{obj_type}:{obj_subtype}:{obj_id}'

    r_lang.sadd(f'objs:langs:{obj_type}', language)
    r_lang.sadd(f'objs:lang:{obj_type}:{obj_subtype}', language)
    # Obj languages
    new = r_lang.sadd(f'obj:lang:{obj_global_id}', language)
    if new:
        # only if no objs_containers, ex: domains
        if not objs_containers:
            r_lang.sadd(f'langs:{obj_type}:{obj_subtype}:{language}', obj_global_id)
        else:
            for global_id in objs_containers:
                _add_container_language(language, global_id, obj_global_id)

def remove_obj_language(language, obj_type, obj_subtype, obj_id, objs_containers=set()):
    if not obj_subtype:
        obj_subtype = ''
    obj_global_id = f'{obj_type}:{obj_subtype}:{obj_id}'
    r_lang.srem(f'obj:lang:{obj_global_id}', language)
    delete_obj_translation(obj_global_id, language)

    if not objs_containers:
        r_lang.srem(f'langs:{obj_type}:{obj_subtype}:{language}', obj_global_id)
        if not r_lang.exists(f'langs:{obj_type}:{obj_subtype}:{language}'):
            r_lang.srem(f'objs:lang:{obj_type}:{obj_subtype}', language)
            _delete_obj_type_stats(language, obj_type, obj_subtype)

    else:
        # REMOVE STATS FROM CONTAINER
        remove_stats_lang = True
        for global_id in objs_containers:
            r = _delete_container_language(language, global_id, obj_global_id)
            if not r:
                remove_stats_lang = False
        if remove_stats_lang:
            r_lang.srem(f'objs:lang:{obj_type}:{obj_subtype}', language)
            _delete_obj_type_stats(language, obj_type, obj_subtype)

def delete_obj_language(obj_type, obj_subtype, obj_id, objs_containers=set()):
    for language in get_obj_languages(obj_type, obj_subtype, obj_id):
        remove_obj_language(language, obj_type, obj_subtype, obj_id, objs_containers=objs_containers)

########################################################################################################################
########################################################################################################################
########################################################################################################################

# TODO handle fields
def detect_obj_language(obj_type, obj_subtype, obj_id, content, objs_containers=set()):
    detector = LanguagesDetector(nb_langs=1)
    language = detector.detect(content)
    if language:
        language = language[0]
        previous_lang = get_obj_languages(obj_type, obj_subtype, obj_id)
        if previous_lang:
            previous_lang = previous_lang.pop()
            if language != previous_lang:
                remove_obj_language(previous_lang, obj_type, obj_subtype, obj_id, objs_containers=objs_containers)
                add_obj_language(language, obj_type, obj_subtype, obj_id, objs_containers=objs_containers)
        else:
            add_obj_language(language, obj_type, obj_subtype, obj_id, objs_containers=objs_containers)
        return language

## Translation
def r_get_obj_translation(obj_global_id, language, field=''):
    return r_lang.hget(f'tr:{obj_global_id}:{field}', language)

def _get_obj_translation(obj_global_id, language, source=None, content=None, field='', objs_containers=set()):
    """
        Returns translated content
    """
    translation = r_cache.get(f'translation:{language}:{obj_global_id}:{field}')
    r_cache.expire(f'translation:{language}:{obj_global_id}:{field}', 0)
    if translation:
        # DEBUG
        # print('cache')
        # r_cache.expire(f'translation:{language}:{obj_global_id}:{field}', 0)
        return translation
    # TODO HANDLE FIELDS TRANSLATION
    translation = r_get_obj_translation(obj_global_id, language, field=field)
    if not translation:
        source, translation = LanguageTranslator().translate(content, source=source, target=language)
        if source:
            obj_type, subtype, obj_id = obj_global_id.split(':', 2)
            add_obj_language(source, obj_type, subtype, obj_id, objs_containers=objs_containers)
    if translation:
        r_cache.set(f'translation:{language}:{obj_global_id}:{field}', translation)
        r_cache.expire(f'translation:{language}:{obj_global_id}:{field}', 300)
    return translation

def get_obj_translation(obj_global_id, language, source=None, content=None, field='', objs_containers=set()):
    return _get_obj_translation(obj_global_id, language, source=source, content=content, field=field, objs_containers=objs_containers)


# TODO Force to edit ????

def set_obj_translation(obj_global_id, language, translation, field=''):
    r_cache.delete(f'translation:{language}:{obj_global_id}:')
    return r_lang.hset(f'tr:{obj_global_id}:{field}', language, translation)

def delete_obj_translation(obj_global_id, language, field=''):
    r_cache.delete(f'translation:{language}:{obj_global_id}:')
    r_lang.hdel(f'tr:{obj_global_id}:{field}', language)

## --LANGUAGE ENGINE-- ##


#### AIL Objects ####
class LanguagesDetector:

    def __init__(self, nb_langs=3, min_proportion=0.2, min_probability=-1, min_len=0):
        lt_url = get_translator_instance()
        if not lt_url:
            self.lt = None
        else:
            self.lt = LibreTranslateAPI(get_translator_instance())
        try:
            self.lt.languages()
        except Exception:
            self.lt = None
        self.detector = gcld3.NNetLanguageIdentifier(min_num_bytes=0, max_num_bytes=1000)
        self.nb_langs = nb_langs
        self.min_proportion = min_proportion
        self.min_probability = min_probability
        self.min_len = min_len

    def detect_gcld3(self, content):
        languages = []
        content = _clean_text_to_translate(content, html=True)
        if self.min_len > 0:
            if len(content) < self.min_len:
                return languages
        # p = self.detector.FindTopNMostFreqLangs(content, num_langs=3)
        # for lang in p:
        #     print(lang.language, lang.probability, lang.proportion, lang.is_reliable)
        # print('------------------------------------------------')
        for lang in self.detector.FindTopNMostFreqLangs(content, num_langs=self.nb_langs):
            if lang.proportion >= self.min_proportion and lang.probability >= self.min_probability and lang.is_reliable:
                languages.append(lang.language)
        return languages

    def detect_lexilang(self, content):
        language, prob = lexilang_detect(content)
        # print(language, prob)
        if prob > 0 and self.min_probability == -1:
            return [language]
        elif prob > 0.4:
            return [language]
        else:
            return []

    def detect_libretranslate(self, content):
        languages = []
        try:
            # [{"confidence": 0.6, "language": "en"}]
            resp = self.lt.detect(content)
        except Exception as e:  # TODO ERROR MESSAGE
            raise Exception(f'libretranslate error: {e}')
            # resp = []
        if resp:
            if isinstance(resp, dict):
                raise Exception(f'libretranslate error {resp}')
            for language in resp:
                if language.confidence >= self.min_probability:
                    languages.append(language)
        return languages

    def detect(self, content, force_gcld3=False, iso3=True):  # TODO detect length between 20-200 ????
        if not content:
            return []
        content = _clean_text_to_translate(content, html=True)
        if not content:
            return []
        # DEBUG
        # print('-------------------------------------------------------')
        # print(content)
        # print(len(content))
        # lexilang
        if len(content) < 150:
            # print('lexilang')
            languages = self.detect_lexilang(content)
        # gcld3
        else:
            # if len(content) >= 200 or not self.lt or force_gcld3:
            # print('gcld3')
            languages = self.detect_gcld3(content)
        # libretranslate
        # else:
        #     languages = self.detect_libretranslate(content)
        if not languages:
            return []
        if iso3:
            langs = []
            for lang in languages:
                iso_lang = convert_iso_code(lang)
                if iso_lang:
                    langs.append(iso_lang)
            return langs
        else:
            return languages

class LanguageTranslator:

    def __init__(self):
        self.lt = LibreTranslateAPI(get_translator_instance())
        self.ld = LanguagesDetector(nb_langs=1)

    def languages(self):
        languages = []
        try:
            for dict_lang in self.lt.languages():
                languages.append({'iso': dict_lang['code'], 'language': dict_lang['name']})
        except Exception as e:
            print(e)
        return languages

    def detect_gcld3(self, content):
        content = _clean_text_to_translate(content, html=True)
        detector = gcld3.NNetLanguageIdentifier(min_num_bytes=0, max_num_bytes=1000)
        lang = detector.FindLanguage(content)
        # print(lang.language)
        # print(lang.is_reliable)
        # print(lang.proportion)
        # print(lang.probability)
        return lang.language

    def detect_libretranslate(self, content):
        try:
            language = self.lt.detect(content)
        except:  # TODO ERROR MESSAGE
            language = None
        if language:
            return language[0].get('language')

    def detect(self, content):
        # print('++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        # print(content)
        language = self.ld.detect(content)
        if language:
            # print(language[0])
            # print('##############################################################')
            return language[0]

    def translate(self, content, source=None, target="en"):  # TODO source target
        if target not in get_translation_languages():
            return None
        translation = None
        if content:
            if not source:
                source = self.detect(content)
            # print(source, content)
            if source:
                if source != target:
                    try:
                        # print(content, source, target)
                        translation = self.lt.translate(content, source, target)
                    except:
                        translation = None
                    # TODO LOG and display error
                    if translation == content:
                        # print('EQUAL')
                        translation = None
        return source, translation


LIST_LANGUAGES = {}
def get_translation_languages():
    global LIST_LANGUAGES
    if not LIST_LANGUAGES:
        try:
            LIST_LANGUAGES = {}
            for lang in LanguageTranslator().languages():
                iso = convert_iso_code(lang['iso'])
                language = get_language_from_iso(iso)
                if language:
                    LIST_LANGUAGES[iso] = language
                # DEBUG
                # else:
                #     print('MISSING LANGUAGE', lang)
                #     print(iso)
                #     print(language)
        except Exception as e:
            print(e)
            LIST_LANGUAGES = {}
    return LIST_LANGUAGES


if __name__ == '__main__':
    t_content = ''
    ddetector = LanguagesDetector(nb_langs=1)
    langg = ddetector.detect(t_content)
    print(langg)

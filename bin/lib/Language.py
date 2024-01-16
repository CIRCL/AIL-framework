#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import re
import sys
import html2text

import gcld3
from libretranslatepy import LibreTranslateAPI

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib.ConfigLoader import ConfigLoader

config_loader = ConfigLoader()
TRANSLATOR_URL = config_loader.get_config_str('Translation', 'libretranslate')
config_loader = None


dict_iso_languages = {
    'af': 'Afrikaans',
    'am': 'Amharic',
    'ar': 'Arabic',
    'bg': 'Bulgarian',
    'bn': 'Bangla',
    'bs': 'Bosnian',
    'ca': 'Catalan',
    'ceb': 'Cebuano',
    'co': 'Corsican',
    'cs': 'Czech',
    'cy': 'Welsh',
    'da': 'Danish',
    'de': 'German',
    'el': 'Greek',
    'en': 'English',
    'eo': 'Esperanto',
    'es': 'Spanish',
    'et': 'Estonian',
    'eu': 'Basque',
    'fa': 'Persian',
    'fi': 'Finnish',
    'fil': 'Filipino',
    'fr': 'French',
    'fy': 'Western Frisian',
    'ga': 'Irish',
    'gd': 'Scottish Gaelic',
    'gl': 'Galician',
    'gu': 'Gujarati',
    'ha': 'Hausa',
    'haw': 'Hawaiian',
    'hi': 'Hindi',
    'hmn': 'Hmong',
    'hr': 'Croatian',
    'ht': 'Haitian Creole',
    'hu': 'Hungarian',
    'hy': 'Armenian',
    'id': 'Indonesian',
    'ig': 'Igbo',
    'is': 'Icelandic',
    'it': 'Italian',
    'iw': 'Hebrew',
    'ja': 'Japanese',
    'jv': 'Javanese',
    'ka': 'Georgian',
    'kk': 'Kazakh',
    'km': 'Khmer',
    'kn': 'Kannada',
    'ko': 'Korean',
    'ku': 'Kurdish',
    'ky': 'Kyrgyz',
    'la': 'Latin',
    'lb': 'Luxembourgish',
    'lo': 'Lao',
    'lt': 'Lithuanian',
    'lv': 'Latvian',
    'mg': 'Malagasy',
    'mi': 'Maori',
    'mk': 'Macedonian',
    'ml': 'Malayalam',
    'mn': 'Mongolian',
    'mr': 'Marathi',
    'ms': 'Malay',
    'mt': 'Maltese',
    'my': 'Burmese',
    'ne': 'Nepali',
    'nl': 'Dutch',
    'no': 'Norwegian',
    'ny': 'Nyanja',
    'pa': 'Punjabi',
    'pl': 'Polish',
    'ps': 'Pashto',
    'pt': 'Portuguese',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sd': 'Sindhi',
    'si': 'Sinhala',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'sm': 'Samoan',
    'sn': 'Shona',
    'so': 'Somali',
    'sq': 'Albanian',
    'sr': 'Serbian',
    'st': 'Southern Sotho',
    'su': 'Sundanese',
    'sv': 'Swedish',
    'sw': 'Swahili',
    'ta': 'Tamil',
    'te': 'Telugu',
    'tg': 'Tajik',
    'th': 'Thai',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'uz': 'Uzbek',
    'vi': 'Vietnamese',
    'xh': 'Xhosa',
    'yi': 'Yiddish',
    'yo': 'Yoruba',
    'zh': 'Chinese',
    'zu': 'Zulu'
}

dict_languages_iso = {
    'Afrikaans': 'af',
    'Amharic': 'am',
    'Arabic': 'ar',
    'Bulgarian': 'bg',
    'Bangla': 'bn',
    'Bosnian': 'bs',
    'Catalan': 'ca',
    'Cebuano': 'ceb',
    'Corsican': 'co',
    'Czech': 'cs',
    'Welsh': 'cy',
    'Danish': 'da',
    'German': 'de',
    'Greek': 'el',
    'English': 'en',
    'Esperanto': 'eo',
    'Spanish': 'es',
    'Estonian': 'et',
    'Basque': 'eu',
    'Persian': 'fa',
    'Finnish': 'fi',
    'Filipino': 'fil',
    'French': 'fr',
    'Western Frisian': 'fy',
    'Irish': 'ga',
    'Scottish Gaelic': 'gd',
    'Galician': 'gl',
    'Gujarati': 'gu',
    'Hausa': 'ha',
    'Hawaiian': 'haw',
    'Hindi': 'hi',
    'Hmong': 'hmn',
    'Croatian': 'hr',
    'Haitian Creole': 'ht',
    'Hungarian': 'hu',
    'Armenian': 'hy',
    'Indonesian': 'id',
    'Igbo': 'ig',
    'Icelandic': 'is',
    'Italian': 'it',
    'Hebrew': 'iw',
    'Japanese': 'ja',
    'Javanese': 'jv',
    'Georgian': 'ka',
    'Kazakh': 'kk',
    'Khmer': 'km',
    'Kannada': 'kn',
    'Korean': 'ko',
    'Kurdish': 'ku',
    'Kyrgyz': 'ky',
    'Latin': 'la',
    'Luxembourgish': 'lb',
    'Lao': 'lo',
    'Lithuanian': 'lt',
    'Latvian': 'lv',
    'Malagasy': 'mg',
    'Maori': 'mi',
    'Macedonian': 'mk',
    'Malayalam': 'ml',
    'Mongolian': 'mn',
    'Marathi': 'mr',
    'Malay': 'ms',
    'Maltese': 'mt',
    'Burmese': 'my',
    'Nepali': 'ne',
    'Dutch': 'nl',
    'Norwegian': 'no',
    'Nyanja': 'ny',
    'Punjabi': 'pa',
    'Polish': 'pl',
    'Pashto': 'ps',
    'Portuguese': 'pt',
    'Romanian': 'ro',
    'Russian': 'ru',
    'Sindhi': 'sd',
    'Sinhala': 'si',
    'Slovak': 'sk',
    'Slovenian': 'sl',
    'Samoan': 'sm',
    'Shona': 'sn',
    'Somali': 'so',
    'Albanian': 'sq',
    'Serbian': 'sr',
    'Southern Sotho': 'st',
    'Sundanese': 'su',
    'Swedish': 'sv',
    'Swahili': 'sw',
    'Tamil': 'ta',
    'Telugu': 'te',
    'Tajik': 'tg',
    'Thai': 'th',
    'Turkish': 'tr',
    'Ukrainian': 'uk',
    'Urdu': 'ur',
    'Uzbek': 'uz',
    'Vietnamese': 'vi',
    'Xhosa': 'xh',
    'Yiddish': 'yi',
    'Yoruba': 'yo',
    'Chinese': 'zh',
    'Zulu': 'zu'
}

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


class LanguageDetector:
    pass

def get_translator_instance():
    return TRANSLATOR_URL

def _get_html2text(content, ignore_links=False):
    h = html2text.HTML2Text()
    h.ignore_links = ignore_links
    h.ignore_images = ignore_links
    return h.handle(content)

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


class LanguagesDetector:

    def __init__(self, nb_langs=3, min_proportion=0.2, min_probability=0.7, min_len=0):
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
        for lang in self.detector.FindTopNMostFreqLangs(content, num_langs=self.nb_langs):
            if lang.proportion >= self.min_proportion and lang.probability >= self.min_probability and lang.is_reliable:
                languages.append(lang.language)
        return languages

    def detect_libretranslate(self, content):
        languages = []
        try:
            # [{"confidence": 0.6, "language": "en"}]
            resp = self.lt.detect(content)
        except:  # TODO ERROR MESSAGE
            resp = []
        if resp:
            for language in resp:
                if language.confidence >= self.min_probability:
                    languages.append(language)
        return languages

    def detect(self, content):
        # gcld3
        if len(content) >= 200 or not self.lt:
            language = self.detect_gcld3(content)
        # libretranslate
        else:
            language = self.detect_libretranslate(content)
        return language

class LanguageTranslator:

    def __init__(self):
        self.lt = LibreTranslateAPI(get_translator_instance())

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
        # gcld3
        if len(content) >= 200:
            language = self.detect_gcld3(content)
        # libretranslate
        else:
            language = self.detect_libretranslate(content)
        return language

    def translate(self, content, source=None, target="en"):  # TODO source target
        if target not in LIST_LANGUAGES:
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
                        print('EQUAL')
                        translation = None
        return translation


LIST_LANGUAGES = {}
def get_translation_languages():
    global LIST_LANGUAGES
    if not LIST_LANGUAGES:
        try:
            LIST_LANGUAGES = {}
            for lang in LanguageTranslator().languages():
                LIST_LANGUAGES[lang['iso']] = lang['language']
        except Exception as e:
            print(e)
            LIST_LANGUAGES = {}
    return LIST_LANGUAGES


if __name__ == '__main__':
    # t_content = ''
    langg = LanguageTranslator()
    # langg = LanguagesDetector()
    # lang.translate(t_content, source='ru')
    langg.languages()

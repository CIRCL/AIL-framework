#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys

import cld3
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

class LanguageTranslator:

    def __init__(self):
        self.lt = LibreTranslateAPI(get_translator_instance())

    def languages(self):
        languages = []
        try:
            for dict_lang in self.lt.languages():
                languages.append({'iso': dict_lang['code'], 'language': dict_lang['name']})
        except:
            pass
        return languages

    def detect_cld3(self, content):
        for lang in cld3.get_frequent_languages(content, num_langs=1):
            return lang.language

    def detect_libretranslate(self, content):
        try:
            language = self.lt.detect(content)
        except:  # TODO ERROR MESSAGE
            language = None
        if language:
            return language[0].get('language')

    def detect(self, content):  # TODO replace by gcld3
        # cld3
        if len(content) >= 200:
            language = self.detect_cld3(content)
        # libretranslate
        else:
            language = self.detect_libretranslate(content)
        return language

    def translate(self, content, source=None, target="en"):  # TODO source target
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


LIST_LANGUAGES = LanguageTranslator().languages()

def get_translation_languages():
    return LIST_LANGUAGES


if __name__ == '__main__':
    t_content = ''
    langg = LanguageTranslator()
    # lang.translate(t_content, source='ru')
    langg.languages()

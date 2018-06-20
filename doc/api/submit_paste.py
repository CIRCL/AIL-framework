#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
submit your own pastes in AIL

empty values must be initialized
'''

import requests

if __name__ == '__main__':

    #AIL url
    url = 'http://localhost:7000'

    ail_url = url + '/PasteSubmit/submit'

    # MIPS TAXONOMIE, need to be initialized (tags_taxonomies = '')
    tags_taxonomies = 'CERT-XLM:malicious-code=\"ransomware\",CERT-XLM:conformity=\"standard\"'

    # MISP GALAXY, need to be initialized (tags_galaxies = '')
    tags_galaxies = 'misp-galaxy:cert-seu-gocsector=\"Constituency\",misp-galaxy:cert-seu-gocsector=\"EU-Centric\"'

    # user paste input, need to be initialized (paste_content = '')
    paste_content = 'paste content test'

    #file full or relative path
    file_to_submit = 'test_file.zip'

    #compress file password, need to be initialized (password = '')
    password = ''

    '''
    submit user text
    '''
    r = requests.post(ail_url, data={   'password': password,
                                        'paste_content': paste_content,
                                        'tags_taxonomies': tags_taxonomies,
                                        'tags_galaxies': tags_galaxies})
    print(r.status_code, r.reason)


    '''
    submit a file
    '''
    with open(file_submit,'rb') as f:

        r = requests.post(ail_url, data={   'password': password,
                                            'paste_content': paste_content,
                                            'tags_taxonomies': tags_taxonomies,
                                            'tags_galaxies': tags_galaxies}, files={'file': (file_to_submit, f.read() )})
        print(r.status_code, r.reason)

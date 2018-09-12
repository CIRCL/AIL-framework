#!/usr/bin/env python3
# -*-coding:UTF-8 -*


from packages import Paste
from Helper import Process
from pubsublogger import publisher

import time
import redis
import newspaper

from collections import defaultdict

from newspaper import fulltext

if __name__ == '__main__':

    publisher.port = 6380
    publisher.channel = "Script"

    publisher.info("Script DomainSubject started")

    config_section = 'DomainSubject'
    p = Process(config_section)

    r_onion = redis.StrictRedis(
        host=p.config.get("ARDB_Onion", "host"),
        port=p.config.getint("ARDB_Onion", "port"),
        db=p.config.getint("ARDB_Onion", "db"),
        decode_responses=True)


    while True:

        # format: <domain>
        domain = p.get_from_set()
        domain = 'easycoinsayj7p5l.onion'

        if domain is not None:

            #retrieve all crawled pastes
            set_crawles_pastes = r_onion.smembers('temp:crawled_domain_pastes:{}'.format(domain))
            if set_crawles_pastes:
                dict_keyword = defaultdict(int)

                for paste_path in set_crawles_pastes:

                    paste = Paste.Paste(paste_path)
                    content = paste.get_p_content()

                    article = newspaper.Article(url='')
                    article.set_html(content)
                    article.parse()
                    article.nlp()

                    for keyword in article.keywords:
                        dict_keyword[keyword] += 1


                if dict_keyword:
                    res = [(k, dict_keyword[k]) for k in sorted(dict_keyword, key=dict_keyword.get, reverse=True)]
                    for item in res:
                        print(item)
                else:
                    print('no keywords found')
            time.sleep(60)

        else:
            time.sleep(5)

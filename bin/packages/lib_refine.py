import gzip, string, sys, os, redis, re
import dns.resolver

from pubsublogger import publisher

from lib_jobs import *
from operator import itemgetter

import numpy as np
import matplotlib.pyplot as plt
from pylab import *

import calendar as cal
from datetime import date, timedelta
from dateutil.rrule import rrule, DAILY



def create_graph_by_day_datastruct(r_serv, r_key, year, month):
    """Creating a datastructure in redis.

    :param r_serv: -- Redis connexion database
    :param r_key: -- (str) The name of the key read in redis (often the name of
    the keywords category list)
    :param year: -- (integer) The year to process
    :param month: -- (integer) The month to process


    """
    a = date(year, month, 01)
    b = date(year, month, cal.monthrange(year, month)[1])

    for dt in rrule(DAILY, dtstart = a, until = b):
        r_serv.zadd(r_key+'_by_day',0,dt.strftime("%Y%m%d"))

    for Tfilename in r_serv.zrange(r_key+'_occur', 0, -1, withscores = True):
        r_serv.zincrby(r_key+'_by_day',
        Tfilename[0][-22:-12].replace('/',''),
        Tfilename[1])




def is_luhn_valid(card_number):
    """Apply the Luhn algorithm to validate credit card.

    :param card_number: -- (int) card number


    """
    r = [int(ch) for ch in str(card_number)][::-1]
    return (sum(r[0::2]) + sum(sum(divmod(d*2,10)) for d in r[1::2])) % 10 == 0




def checking_MX_record(r_serv, adress_set):
    """Check if emails MX domains are responding.

    :param r_serv: -- Redis connexion database
    :param adress_set: -- (set) This is a set of emails adress
    :return: (int) Number of adress with a responding and valid MX domains

    This function will split the email adress and try to resolve their domains
    names: on example@gmail.com it will try to resolve gmail.com

    """
    score = 0
    num = len(adress_set)
    WalidMX = set([])
    # Transforming the set into a string
    MXdomains = re.findall("@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,20}", str(adress_set).lower())

    if MXdomains != []:

            for MXdomain in set(MXdomains):
                try:
                    #Already in Redis living.
                    if r_serv.exists(MXdomain[1:]):
                        score += 1
                        WalidMX.add(MXdomain[1:])
                    # Not already in Redis
                    else:
                        # If I'm Walid MX domain
                        if dns.resolver.query(MXdomain[1:], rdtype = dns.rdatatype.MX):
                            # Gonna be added in redis.
                            r_serv.setex(MXdomain[1:],timedelta(days=1),1)
                            score += 1
                            WalidMX.add(MXdomain[1:])
                        else:
                            pass

                except dns.resolver.NoNameservers:
                    publisher.debug('NoNameserver, No non-broken nameservers are available to answer the query.')

                except dns.resolver.NoAnswer:
                    publisher.debug('NoAnswer, The response did not contain an answer to the question.')

                except dns.name.EmptyLabel:
                    publisher.debug('SyntaxError: EmptyLabel')

                except dns.resolver.NXDOMAIN:
                    publisher.debug('The query name does not exist.')

                except dns.name.LabelTooLong:
                    publisher.debug('The Label is too long')

                finally:
                    pass

    publisher.debug("emails before: {0} after: {1} (valid)".format(num, score))
    return (num, WalidMX)




def checking_A_record(r_serv, domains_set):
    score = 0
    num = len(domains_set)
    WalidA = set([])

    for Adomain in domains_set:
        try:
            #Already in Redis living.
            if r_serv.exists(Adomain):
                score += 1
                WalidA.add(Adomain)
            # Not already in Redis
            else:
                # If I'm Walid domain
                if dns.resolver.query(Adomain, rdtype = dns.rdatatype.A):
                    # Gonna be added in redis.
                    r_serv.setex(Adomain,timedelta(days=1),1)
                    score += 1
                    WalidA.add(Adomain)
                else:
                    pass

        except dns.resolver.NoNameservers:
            publisher.debug('NoNameserver, No non-broken nameservers are available to answer the query.')

        except dns.resolver.NoAnswer:
            publisher.debug('NoAnswer, The response did not contain an answer to the question.')

        except dns.name.EmptyLabel:
            publisher.debug('SyntaxError: EmptyLabel')

        except dns.resolver.NXDOMAIN:
            publisher.debug('The query name does not exist.')

        except dns.name.LabelTooLong:
            publisher.debug('The Label is too long')

        finally:
            pass

    publisher.debug("URLs before: {0} after: {1} (valid)".format(num, score))
    return (num, WalidA)




def refining_regex_dataset(r_serv, r_key, regex, min_match, year, month, luhn = True, dnscheck = True):
    """Refine the "raw dataset" of paste with regulars expressions

    :param r_serv: -- Redis connexion database
    :param r_key: -- (str) The name of the key read in redis (often the name of
        the keywords category list)
    :param min_match: -- (int) Below this number file are deleted
    :param regex: -- Regular expression which will be match.

    This function Refine database created with classify_token_paste function.
    It opening again the files which matchs the keywords category list, found
    regular expression inside it and count how many time is found.

    If there is not too much match about the regular expression the file is
    deleted from the list.

    Than it finally merge the result by day to be able to create a bar graph
    which will represent how many occurence by day the regex match.

    """
    for filename in r_serv.zrange(r_key, 0, -1):

        with gzip.open(filename, 'rb') as F:
            var = 0
            matchs = set([])

            for num, kword in enumerate(F):

                match = re.findall(regex, kword)
                var += len(match)

                for y in match:
                    if y != '' and len(y) < 100:
                        matchs.add(y)
            # If there is less match than min_match delete it (False pos)
            if len(matchs) <= min_match :
                r_serv.zrem(r_key, filename)
                publisher.debug("{0} deleted".format(filename))
            else:
            # else changing the score.
                if r_key == "creditcard_categ" and luhn:
                    for card_number in matchs:
                        if is_luhn_valid(card_number):

                            r_serv.zincrby(r_key+'_occur', filename, 1)

                            publisher.info("{1} is valid in the file {0}".format(filename, card_number))
                        else:
                            publisher.debug("{0} card is invalid".format(card_number))

                if r_key == "mails_categ" and dnscheck:
                    r_serv.zadd(r_key+'_occur', checking_MX_record(r_serv, matchs), filename)

                else:
                    # LUHN NOT TRIGGERED (Other Categs)
                    r_serv.zadd(r_key+'_occur',
                        len(matchs),
                        filename)

    create_graph_by_day_datastruct(r_serv, r_key, year, month)




def graph_categ_by_day(r_serv, filename, year, month, r_key):
    """Create a bargraph representing regex matching by day

    :param r_serv: -- Redis connexion database
    :param filename: -- (str) The absolute path where to save the figure.png
    :param r_key: -- (str) The name of the key read in redis (often the name of
        the keywords category list)
    :param year: -- (integer) The year to process
    :param month: -- (integer) The month to process

    This function display the amount of the category per day.

    """
    adate = []
    categ_num = []
    rcParams['figure.figsize'] = 15, 10

    a = date(year, month, 01)
    b = date(year, month, cal.monthrange(year, month)[1])

    for dt in rrule(DAILY, dtstart = a, until = b):
        adate.append(dt.strftime("%d"))
        categ_num.append(r_serv.zscore(r_key+'_by_day',dt.strftime("%Y%m%d")))

    n_groups = len(categ_num)
    adress_scores = tuple(categ_num)

    index = np.arange(n_groups)
    bar_width = 0.5
    opacity = 0.6

    ladress = plt.bar(index, adress_scores, bar_width,
                 alpha = opacity,
                 color = 'b',
                 label = r_key)


    plt.plot(tuple(categ_num), 'r--')
    #plt.yscale('log')
    plt.xlabel('Days')
    plt.ylabel('Amount')
    plt.title('Occurence of '+r_key+' by day')
    plt.xticks(index + bar_width/2 , tuple(adate))

    plt.legend()
    plt.grid()

    plt.tight_layout()

    plt.savefig(filename+".png", dpi=None, facecolor='w', edgecolor='b',
        orientation='portrait', papertype=None, format="png",
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=True)

    publisher.info(filename+".png"+" saved!")




def create_tld_list(url = "https://mxr.mozilla.org/mozilla-central/source/netwerk/dns/effective_tld_names.dat?raw=1"):
    """Recover a tld list from url.

    :param url: -- The url of the tld list.
    :return: -- list

    This function recover from mozilla.org the list of the effective tld names,
    Save it as a file, and return a list of all the tld.


    """
    domains = []
    htmlSource = urllib.urlopen(url).read()
    with open("ICCANdomain", 'wb') as F:
        F.write(htmlSource)

    with open("ICCANdomain", 'rb') as F:

        for num, line in enumerate(F):
            if re.match(r"^\/\/|\n", line) == None:
                domains.append(re.sub(r'\*', '', line[:-1]))
            else:
                publisher.info("Comment line ignored.")

    return domains

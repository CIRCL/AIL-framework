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

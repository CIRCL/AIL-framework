#!/usr/bin/python3

import os
import sys
import dns.resolver
import dns.exception
import logging.config

from datetime import timedelta

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from lib import ail_logger
from lib import ConfigLoader


logging.config.dictConfig(ail_logger.get_config(name='modules'))
logger = logging.getLogger()

config_loader = ConfigLoader.ConfigLoader()
dns_server = config_loader.get_config_str("DomClassifier", "dns")
config_loader = None

def is_luhn_valid(card_number):
    """Apply the Luhn algorithm to validate credit card.

    :param card_number: -- (int) card number


    """
    r = [int(ch) for ch in str(card_number)][::-1]
    return (sum(r[0::2]) + sum(sum(divmod(d*2, 10)) for d in r[1::2])) % 10 == 0


def checking_MX_record(r_serv, MXdomains, addr_dns):
    """Check if emails MX domains are responding.

    :param r_serv: -- Redis connexion database
    :param adress_set: -- (set) This is a set of emails adress
    :return: (int) Number of adress with a responding and valid MX domains

    This function will split the email adress and try to resolve their domains
    names: on example@gmail.com it will try to resolve gmail.com

    """

    score = 0
    WalidMX = set([])
    validMX = {}
    num = len(MXdomains)
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [addr_dns]
    resolver.timeout = 5.0
    resolver.lifetime = 2.0
    if MXdomains != []:

            for MXdomain in MXdomains:
                try:
                    MXdomain = MXdomain[1:]
                    # Already in Redis living.
                    if r_serv.exists(MXdomain):
                        score += 1
                        WalidMX.add(MXdomain)
                        validMX[MXdomain] = validMX.get(MXdomain, 0) + 1
                    # Not already in Redis
                    else:
                        # If I'm Walid MX domain
                        if resolver.query(MXdomain, rdtype=dns.rdatatype.MX):
                            # Gonna be added in redis.
                            r_serv.setex(MXdomain, 1, timedelta(days=1))
                            score += 1
                            WalidMX.add(MXdomain)
                            validMX[MXdomain] = validMX.get(MXdomain, 0) + 1
                        else:
                            pass

                except dns.resolver.NoNameservers:
                    logger.debug('NoNameserver, No non-broken nameservers are available to answer the query.')
                    print('NoNameserver, No non-broken nameservers are available to answer the query.')

                except dns.resolver.NoAnswer:
                    logger.debug('NoAnswer, The response did not contain an answer to the question.')
                    print('NoAnswer, The response did not contain an answer to the question.')

                except dns.name.EmptyLabel:
                    logger.debug('SyntaxError: EmptyLabel')
                    print('SyntaxError: EmptyLabel')

                except dns.resolver.NXDOMAIN:
                    r_serv.setex(MXdomain[1:], 1, timedelta(days=1))
                    logger.debug('The query name does not exist.')
                    print('The query name does not exist.')

                except dns.name.LabelTooLong:
                    logger.debug('The Label is too long')
                    print('The Label is too long')

                except dns.exception.Timeout:
                    print('dns timeout')
                    r_serv.setex(MXdomain, 1, timedelta(days=1))

                except Exception as e:
                    print(e)

    logger.debug("emails before: {0} after: {1} (valid)".format(num, score))
    #return (num, WalidMX)
    return (num, validMX)


def checking_A_record(r_serv, domains_set):

    score = 0
    num = len(domains_set)
    WalidA = set([])
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    resolver.timeout = 5.0
    resolver.lifetime = 2.0

    for Adomain in domains_set:
        try:
            # Already in Redis living.
            if r_serv.exists(Adomain):
                score += 1
                WalidA.add(Adomain)
            # Not already in Redis
            else:
                # If I'm Walid domain
                if resolver.query(Adomain, rdtype=dns.rdatatype.A):
                    # Gonna be added in redis.
                    r_serv.setex(Adomain, 1, timedelta(days=1))
                    score += 1
                    WalidA.add(Adomain)
                else:
                    pass

        except dns.resolver.NoNameservers:
            logger.debug('NoNameserver, No non-broken nameservers are available to answer the query.')

        except dns.resolver.NoAnswer:
            logger.debug('NoAnswer, The response did not contain an answer to the question.')

        except dns.name.EmptyLabel:
            logger.debug('SyntaxError: EmptyLabel')

        except dns.resolver.NXDOMAIN:
            r_serv.setex(Adomain[1:], 1, timedelta(days=1))
            logger.debug('The query name does not exist.')

        except dns.name.LabelTooLong:
            logger.debug('The Label is too long')

        except Exception as e:
            print(e)

    logger.debug("URLs before: {0} after: {1} (valid)".format(num, score))
    return (num, WalidA)

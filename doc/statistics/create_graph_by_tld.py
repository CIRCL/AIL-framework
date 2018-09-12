#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
Create statistics pie charts by tld

Default tld: lu
'''

import os
import sys
import redis
import argparse
import datetime
import heapq
import operator
import matplotlib.pyplot as plt
import numpy as np

sys.path.append(os.environ['AIL_BIN'])

from Helper import Process

def create_pie_chart(country ,db_key, date, pie_title, path, save_name):

    monthly_credential_by_tld = server_statistics.hkeys(db_key + date)

    l_tld = []
    for tld in monthly_credential_by_tld:
        nb_tld = server_statistics.hget(db_key + date, tld)
        if nb_tld is not None:
            nb_tld = int(nb_tld)
        else:
            nb_tld = 0
        l_tld.append( (tld, nb_tld) )

    mail_tld_top5 = heapq.nlargest(5, l_tld, key=operator.itemgetter(1))

    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    labels = []
    sizes = []
    explode = []  # only "explode" the 2nd slice (i.e. 'Hogs')
    explode_value = 0
    for tld in mail_tld_top5:
        labels.append(tld[0] +' ('+str(tld[1])+')')
        sizes.append(tld[1])
        explode.append(explode_value)
        explode_value = explode_value +0.1

    nb_tld = server_statistics.hget(db_key + date, country)
    if nb_tld is not None:
        nb_tld = int(nb_tld)
    else:
        nb_tld = 0
    country_label = country + ' ('+str(nb_tld)+')'
    if country_label not in labels:
        labels.append(country_label)
        sizes.append(nb_tld)
        explode.append(explode_value)
    explode = tuple(explode)

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    ax1.set_title(pie_title)
    #plt.show()
    plt.savefig(os.path.join(path,save_name))
    plt.close(fig1)

def create_donut_chart(db_key, date, pie_title, path, save_name):

    monthly_credential_by_tld = server_statistics.hkeys(db_key + date)
    print()

    l_tld = []
    for tld in monthly_credential_by_tld:
        nb_tld = server_statistics.hget(db_key + date, tld)
        if nb_tld is not None:
            nb_tld = int(nb_tld)
        else:
            nb_tld = 0
        l_tld.append( (tld, nb_tld) )

    mail_tld_top5 = heapq.nlargest(5, l_tld, key=operator.itemgetter(1))

    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    recipe = []
    data = []
    for tld in mail_tld_top5:
        recipe.append(tld[0])
        data.append(tld[1])

    nb_tld = server_statistics.hget(db_key + date, country)
    if nb_tld is not None:
        nb_tld = int(nb_tld)
    else:
        nb_tld = 0
    if country not in recipe:
        recipe.append(country)
        data.append(nb_tld)

    fig1, ax1 = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))

    wedges, texts = ax1.pie(data, wedgeprops=dict(width=0.5), startangle=-40)

    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(xycoords='data', textcoords='data', arrowprops=dict(arrowstyle="-"),
              bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax1.annotate(recipe[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
                     horizontalalignment=horizontalalignment, **kw)

    ax1.set_title(pie_title)
    #plt.show()
    plt.savefig(os.path.join(path, save_name))
    plt.close(fig1)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='''This script is a part of the Analysis Information Leak
        framework. Create statistics pie charts".''',
        epilog='Example: ./create_lu_graph.py 0 lu now, create_lu_graph.py 0 lu 201807')

    parser.add_argument('type', type=int, default=0,
                        help='''The graph type (default 0),
                        0: all,
                        1: credential_pie,
                        2: mail_pie
                        3: sqlinjection_pie,
                        4: iban_pie,''',
                        choices=[0, 1, 2, 3, 4], action='store')

    parser.add_argument('country', type=str, default="lu",
                        help='''The country code, lu:default''',
                        action='store')

    parser.add_argument('date', type=str, default="now",
                        help='''month %Y%m, example: 201810''', action='store')

    args = parser.parse_args()

    path = os.path.join(os.environ['AIL_HOME'], 'doc', 'statistics') # save path

    config_section = 'ARDB_Statistics'

    p = Process(config_section, False)

    # ARDB #
    server_statistics = redis.StrictRedis(
        host=p.config.get("ARDB_Statistics", "host"),
        port=p.config.getint("ARDB_Statistics", "port"),
        db=p.config.getint("ARDB_Statistics", "db"),
        decode_responses=True)

    if args.date == 'now' or len(args.date) != 6:
        date = datetime.datetime.now().strftime("%Y%m")
    else:
        date = args.date

    if args.type == 0:
        create_pie_chart(args.country, 'credential_by_tld:', date, "AIL: Credential leak by tld", path, 'AIL_credential_by_tld.png')
        create_pie_chart(args.country, 'mail_by_tld:', date, "AIL: mail leak by tld", path, 'AIL_mail_by_tld.png')
        create_pie_chart(args.country, 'SQLInjection_by_tld:', date, "AIL: SQLInjection by tld", path, 'AIL_SQLInjection_by_tld.png')
        create_pie_chart(args.country.upper(), 'iban_by_country:', date, "AIL: Iban by country", path, 'AIL_iban_by_country.png')
    elif args.type == 1:
        create_pie_chart(args.country, 'credential_by_tld:', date, "AIL: Credential leak by tld", path, 'AIL_credential_by_tld.png')
    elif args.type == 2:
        create_pie_chart(args.country, 'mail_by_tld:', date, "AIL: mail leak by tld", path, 'AIL_mail_by_tld.png')
    elif args.type == 3:
        create_pie_chart(args.country, 'SQLInjection_by_tld:', date, "AIL: sqlInjection by tld", path, 'AIL_sqlInjectionl_by_tld.png')
    elif args.type == 4:
        create_pie_chart(args.country.upper(), 'iban_by_country:', date, "AIL: Iban by country", path, 'AIL_iban_by_country.png')

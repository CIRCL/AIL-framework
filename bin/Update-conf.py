#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import ConfigParser
from ConfigParser import RawConfigParser
import os


def main():

    configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
    if not os.path.exists(configfile):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')
    configfileSample  = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg.sample')

    cfg = ConfigParser.ConfigParser()
    cfg.read(configfile)
    cfgSample = ConfigParser.ConfigParser()
    cfgSample.read(configfileSample)

    sections = RawConfigParser.sections(cfg)
    sectionsSample = RawConfigParser.sections(cfgSample)
    
    missingSection = []
    dicoMissingSection = {}
    missingItem = []
    dicoMissingItem = {}

    for sec in sectionsSample:
        if sec not in sections:
            missingSection += [sec]
            dicoMissingSection[sec] = RawConfigParser.items(cfgSample, sec)
        else:
            setSample = set(RawConfigParser.options(cfgSample, sec))
            setNormal = set(RawConfigParser.options(cfg, sec))
            if setSample != setNormal:
                missing_items = list(setSample.difference(setNormal))
                missingItem += [sec]
                list_items = []
                for i in missing_items:
                    list_items.append( (i, cfgSample.get(sec, i)) )
                dicoMissingItem[sec] = list_items

    if len(missingSection) == 0 and len(missingItem) == 0:
        print("Configuration up-to-date")
        return
    print("/!\\ Configuration not complete. Missing following configuration: /!\\")
    print("+--------------------------------------------------------------------+")
    for section in missingSection:
        print("["+section+"]")
        for item in dicoMissingSection[section]:
            print("  - "+item[0])
    for section in missingItem:
        print("["+section+"]")
        for item in dicoMissingItem[section]:
            print("  - "+item[0])
    print("+--------------------------------------------------------------------+")
    resp = raw_input("Do you want to auto fix it? [y/n] ")

    if resp != 'y':
        return
    else:
        for section in missingSection:
            cfg.add_section(section)
            for item, value in dicoMissingSection[section]:
                cfg.set(section, item, value)
        for section in missingItem:
            for item, value in dicoMissingItem[section]:
                cfg.set(section, item, value)

        with open(configfile, 'w') as f:
            cfg.write(f)


if __name__ == "__main__":
    main()


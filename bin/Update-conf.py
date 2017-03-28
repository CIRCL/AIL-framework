#!/usr/bin/env python2
# -*-coding:UTF-8 -*

import ConfigParser
from ConfigParser import ConfigParser as cfgP
import os
from collections import OrderedDict


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

    sections = cfgP.sections(cfg)
    sectionsSample = cfgP.sections(cfgSample)
    
    missingSection = []
    dicoMissingSection = {}
    missingItem = []
    dicoMissingItem = {}

    for sec in sectionsSample:
        if sec not in sections:
            missingSection += [sec]
            dicoMissingSection[sec] = cfgP.items(cfgSample, sec)
        else:
            setSample = set(cfgP.options(cfgSample, sec))
            setNormal = set(cfgP.options(cfg, sec))
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
        #Do not keep item order in section. New items appened
        for section in missingItem:
            for item, value in dicoMissingItem[section]:
                cfg.set(section, item, value)

        #Keep sections order while updating the config file
        new_dico = add_items_to_correct_position(cfgSample._sections, cfg._sections, missingSection, dicoMissingSection)
        cfg._sections = new_dico

        with open(configfile, 'w') as f:
            cfg.write(f)


''' Return a new dico with the section ordered as the old configuration with the updated one added '''
def add_items_to_correct_position(sample_dico, old_dico, missingSection, dicoMissingSection):
    new_dico = OrderedDict()
    
    positions = {}
    for pos_i, sec in enumerate(sample_dico):
        if sec in missingSection:
            positions[pos_i] = sec

    for pos_i, sec in enumerate(old_dico):
        if pos_i in positions:
            missSection = positions[pos_i]
            new_dico[missSection] = sample_dico[missSection]

        new_dico[sec] = old_dico[sec]
    return new_dico


if __name__ == "__main__":
    main()


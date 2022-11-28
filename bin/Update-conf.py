#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import configparser

def print_message(message_to_print, verbose):
    if verbose:
        print(message_to_print)

def update_config(config_file, config_file_sample, config_file_backup=False):

    verbose = True

    # Check if confile file exist
    if not os.path.isfile(config_file):
        # create config file
        with open(config_file, 'w') as configfile:
            with open(config_file_sample, 'r') as config_file_sample:
                configfile.write(config_file_sample.read())
        print_message('Config File Created', verbose)
    else:
        config_server = configparser.ConfigParser()
        config_server.read(config_file)
        config_sections = config_server.sections()

        config_sample = configparser.ConfigParser()
        config_sample.read(config_file_sample)
        sample_sections = config_sample.sections()

        mew_content_added = False
        for section in sample_sections:
            new_key_added = False
            if section not in config_sections:
                # add new section
                config_server.add_section(section)
                mew_content_added = True
            for key in config_sample[section]:
                if key not in config_server[section]:
                    # add new section key
                    config_server.set(section, key, config_sample[section][key])
                    if not new_key_added:
                        print_message('[{}]'.format(section), verbose)
                        new_key_added = True
                        mew_content_added = True
                    print_message('    {} = {}'.format(key, config_sample[section][key]), verbose)

        # new keys have been added to config file
        if mew_content_added:
            # backup config file
            if config_file_backup:
                with open(config_file_backup, 'w') as configfile:
                    with open(config_file, 'r') as configfile_origin:
                        configfile.write(configfile_origin.read())
                print_message('New Backup Created', verbose)
            # create new config file
            with open(config_file, 'w') as configfile:
                config_server.write(configfile)
            print_message('Config file updated', verbose)
        else:
            print_message('Config File: Nothing to update', verbose)


# return true if the configuration is up-to-date
def main():

    config_file_default = os.path.join(os.environ['AIL_HOME'], 'configs/core.cfg')
    config_file_default_sample = os.path.join(os.environ['AIL_HOME'], 'configs/core.cfg.sample')
    config_file_default_backup = os.path.join(os.environ['AIL_HOME'], 'configs/core.cfg.backup')

    config_file_update = os.path.join(os.environ['AIL_HOME'], 'configs/update.cfg')
    config_file_update_sample = os.path.join(os.environ['AIL_HOME'], 'configs/update.cfg.sample')

    if not os.path.exists(config_file_default_sample):
        raise Exception('Unable to find the configuration file. \
                        Did you set environment variables? \
                        Or activate the virtualenv.')

    update_config(config_file_default, config_file_default_sample, config_file_backup=config_file_default_backup)
    update_config(config_file_update, config_file_update_sample)

    return True


if __name__ == "__main__":
    if main():
        sys.exit()
    else:
        sys.exit(1)

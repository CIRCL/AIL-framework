#!/usr/bin/python3

import os
import json
import requests
import configparser

misp_module_url = 'http://localhost:6666'

default_config_path = os.path.join(os.environ['AIL_HOME'], 'configs', 'misp_modules.cfg')

def init_config(config_path=default_config_path):
    config = configparser.ConfigParser()
    if os.path.isfile(config_path):
        config.read(config_path)
    else:
        config.add_section('misp_modules')
        config.set('misp_modules', 'url', 'http://localhost')
        config.set('misp_modules', 'port', '6666')
    return config

def init_module_config(module_json, config, config_path=default_config_path):
    if 'config' in module_json['meta']:
        if module_json['meta']['config']:
            if module_json['name'] not in config:
                config.add_section(module_json['name'])
            for config_var in module_json['meta']['config']:
                if config_var not in config[module_json['name']]:
                    config.set(module_json['name'], config_var, '')
        else:
            print(module_json['name'])
    return config

def misp_module_enrichement(misp_module_url, misp_module_port, request_content):
    endpoint_url = '{}:{}/query'.format(misp_module_url, misp_module_port)
    req = requests.post(endpoint_url, headers={'Content-Type': 'application/json'}, data=request_content)
    print(req.json())

if __name__ == "__main__":
    req = requests.get('{}/modules'.format(misp_module_url))

    if req.status_code == 200:
        all_misp_modules = req.json()
        all_modules = []
        for module_json in all_misp_modules:

            #filter module-types
            if 'hover' in module_json['meta']['module-type']:
                all_modules.append(module_json)

            # if 'expansion' in module_json['meta']['module-type']:
            #     all_expansion.append(module_json['name'])

        config = init_config()
        for module_json in all_modules:
            config = init_module_config(module_json, config, config_path=default_config_path)

        with open(default_config_path, 'w') as f:
            config.write(f)

        misp_module_url = 'http://localhost'
        misp_module_port = 6666
        test_content = json.dumps({'module': 'btc_steroids', 'btc': '1hmZdUYHyqH3DmWyduRRW3HT8Vm6PHsD1'})
        misp_module_enrichement(misp_module_url, misp_module_port, test_content)


    else:
        print('Error: Module service not reachable.')
        print(req)

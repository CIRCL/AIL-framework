#!/usr/bin/env python3
# -*-coding:UTF-8 -*

"Hepler to create a new webpage associated with a module."

import os

def createModuleFolder(modulename):
    path_module = os.path.join('modules', modulename)
    os.mkdir(path_module)

    # create html template
    with open('templates/base_template.html', 'r') as templateFile:
        template = templateFile.read()
        template = template.replace('MODULENAME', modulename)

    os.mkdir(os.path.join(path_module, 'templates'))
    with open(os.path.join(os.path.join(path_module, 'templates'), modulename+'.html'), 'w') as toWriteTemplate:
        toWriteTemplate.write(template)

    # create html header template
    with open('templates/header_base_template.html', 'r') as header_templateFile:
        header = header_templateFile.read()
        header = header.replace('MODULENAME', modulename)

    with open(os.path.join(os.path.join(path_module, 'templates'), 'header_{}.html'.format(modulename) ), 'w') as toWriteHeader:
        toWriteHeader.write(header)


    #create flask template
    with open('Flask_base_template.py', 'r') as flaskFile:
        flask = flaskFile.read()
        flask = flask.replace('MODULENAME', modulename)

    with open(os.path.join(path_module, 'Flask_{}.py'.format(modulename)), 'w') as toWriteFlask:
        toWriteFlask.write(flask)


def main():
	rep1 = input('New module name: ')
	createModuleFolder(rep1)

if __name__ == '__main__':
	main()

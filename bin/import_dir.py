#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
import base64
import StringIO
import gzip
import argparse
import os
import time, datetime
import mimetypes

'''
'
'   Import content/pastes into redis.
'   If content is not compressed yet, compress it.
'
'   /!\ WARNING /!\
        Content to be imported must be placed in a directory tree of the form
        root/
        |
        +-- Year/
            |
            +-- Month/
                |
                +-- Day/
                    |
                    +-- Content
    e.g.:
    ~/to_import/2017/08/22/paste1.gz
'
'''

import StringIO
import gzip
def is_hierachy_valid(path):
    var = path.split('/')
    try:
        newDate = datetime.datetime(int(var[-4]), int(var[-3]), int(var[-2]))
        correctDate = True
    except ValueError:
        correctDate = False
    except IndexError:
        correctDate = False
    except:
        correctDate = False
    return correctDate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Take files from a directory and push them into a 0MQ feed.')
    parser.add_argument('-d', '--directory', type=str, required=True, help='Root directory to import')
    parser.add_argument('-p', '--port', type=int, default=5556, help='Zero MQ port')
    parser.add_argument('-c', '--channel', type=str, default='102', help='Zero MQ channel')
    parser.add_argument('-n', '--name', type=str, default='import_dir', help='Name of the feeder')
    parser.add_argument('-s', '--seconds', type=float, default=0.2, help='Second between pastes')
    parser.add_argument('--hierarchy', type=int, default=1, help='Number of parent directory forming the name')

    args = parser.parse_args()

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:{}".format(args.port))
    time.sleep(1) #Important, avoid loosing the 1 message

    for dirname, dirnames, filenames in os.walk(args.directory):
        for filename in filenames:
            complete_path = os.path.join(dirname, filename)

            #take wanted path of the file
            wanted_path = os.path.realpath(complete_path)
            wanted_path = wanted_path.split('/')
            wanted_path = '/'.join(wanted_path[-(4+args.hierarchy):])

            messagedata = open(complete_path).read()

            #if paste do not have a 'date hierarchy' ignore it
            if not is_hierachy_valid(complete_path):
                print('/!\ hierarchy not valid, should have the format yyyy/mm/dd/paste.gz /!\ ')
                print(complete_path)
                break

            #verify that the data is gzipEncoded. if not compress it
            if 'text' in str(mimetypes.guess_type(complete_path)[0]):
                out = StringIO.StringIO()
                with gzip.GzipFile(fileobj=out, mode="w") as f:
                    f.write(messagedata)
                messagedata = out.getvalue()
                wanted_path += '.gz'

            print(args.name+'>'+wanted_path)
            path_to_send = args.name + '>' + wanted_path
            socket.send('{} {} {}'.format(args.channel, path_to_send, base64.b64encode(messagedata)))
            time.sleep(args.seconds)

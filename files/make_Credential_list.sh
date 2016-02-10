#!/bin/bash

set -e

while read line; do
    echo $line
    echo -n $line | md5sum | cut -d' ' -f 1
    echo -n $line | sha1sum | cut -d' ' -f 1
    echo -n $line | sha256sum | cut -d' ' -f 1
done < top_pwd_clear > Credential

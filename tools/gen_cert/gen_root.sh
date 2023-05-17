#!/usr/bin/env bash 
# Create Root key
openssl genrsa -out rootCA.key 4096
# Create and Sign the Root CA Certificate
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 1024 -out rootCA.crt -config san.cnf

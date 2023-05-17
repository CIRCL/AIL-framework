#!/usr/bin/env bash
# Create Server key
openssl genrsa -out server.key 4096
# Create the Server Signing Request - non interactive, config in san.cnf
openssl req -sha256 -new -key server.key -out server.csr -config san.cnf
# Create the server certificate by rootCA, with ext3 subjectAltName in ext3.cnf
openssl x509 -req -in server.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out server.crt -days 500 -sha256 -extfile ext3.cnf
# Concat in pem
cat server.crt server.key > server.pem

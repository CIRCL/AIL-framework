#!/bin/bash

set -e
set -x

screen -dmS "Script"
sleep 0.1

echo -e $GREEN"\t* Launching ZMQ scripts"$DEFAULT

screen -S "Script" -X screen -t "Global" bash -c './Global.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Duplicate" bash -c './Duplicate_ssdeep_v2.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Attribute" bash -c './Attribute.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Line" bash -c './Line.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "DomainClassifier" bash -c './DomClassifier.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Categ" bash -c './Categ.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Tokenize" bash -c './Tokenize.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "CreditCard" bash -c './CreditCard.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Onion" bash -c './Onion.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Mail" bash -c './Mail.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Url" bash -c './Url.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Credential" bash -c './Credential.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Curve" bash -c './Curve.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Curve_topsets_manager" bash -c './Curve_manage_top_sets.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Indexer" bash -c './Indexer.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Keys" bash -c './Keys.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Phone" bash -c './Phone.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Release" bash -c './Release.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Cve" bash -c './Cve.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "WebStats" bash -c './WebStats.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "ModuleStats" bash -c './ModuleStats.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "SQLInjectionDetection" bash -c './SQLInjectionDetection.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "Browse_warning_paste" bash -c './Browse_warning_paste.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "SentimentAnalyser" bash -c './SentimentAnalyser.py; read x'

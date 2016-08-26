#!/bin/bash

set -e
set -x

screen -dmS "Script"
sleep 0.1

echo -e $GREEN"\t* Launching ZMQ scripts"$DEFAULT

    screen -S "Script" -X screen -t "ModuleInformation" bash -c './ModuleInformation.py -k 0 -c 1; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Global" bash -c './Global.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Duplicates" bash -c './Duplicates.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Attributes" bash -c './Attributes.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Lines" bash -c './Lines.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "DomClassifier" bash -c './DomClassifier.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Categ" bash -c './Categ.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Tokenize" bash -c './Tokenize.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "CreditCards" bash -c './CreditCards.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Onion" bash -c './Onion.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Mail" bash -c './Mail.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Web" bash -c './Web.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Credential" bash -c './Credential.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Curve" bash -c './Curve.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "CurveManageTopSets" bash -c './CurveManageTopSets.py; read x'
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
    screen -S "Script" -X screen -t "SentimentAnalysis" bash -c './SentimentAnalysis.py; read x'

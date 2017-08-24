#!/bin/bash

set -e
set -x

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_REDIS" ] && echo "Needs the env var AIL_REDIS. Run the script from the virtual environment." && exit 1;
[ -z "$AIL_LEVELDB" ] && echo "Needs the env var AIL_LEVELDB. Run the script from the virtual environment." && exit 1;

echo -e "\t* Checking configuration"
bash -c "./Update-conf.py"
exitStatus=$?
if [ $exitStatus -ge 1 ]; then
    echo -e $RED"\t* Configuration not up-to-date"$DEFAULT
    exit
fi
echo -e $GREEN"\t* Configuration up-to-date"$DEFAULT

screen -dmS "Script"
sleep 0.1
echo -e $GREEN"\t* Launching ZMQ scripts"$DEFAULT

screen -S "Script" -X screen -t "ModuleInformation" bash -c './ModulesInformationV2.py -k 0 -c 1; read x'
sleep 0.1
screen -S "Script" -X screen -t "Mixer" bash -c './Mixer.py; read x'
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
screen -S "Script" -X screen -t "RegexForTermsFrequency" bash -c './RegexForTermsFrequency.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "SetForTermsFrequency" bash -c './SetForTermsFrequency.py; read x'
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
screen -S "Script" -X screen -t "BrowseWarningPaste" bash -c './BrowseWarningPaste.py; read x'
sleep 0.1
screen -S "Script" -X screen -t "SentimentAnalysis" bash -c './SentimentAnalysis.py; read x'

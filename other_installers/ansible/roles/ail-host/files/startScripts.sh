#!/bin/bash

# Wait for all redis instances to start
while true; do redis-cli -p 6379 PING && break; sleep 1; done
while true; do redis-cli -p 6380 PING && break; sleep 1; done
while true; do redis-cli -p 6381 PING && break; sleep 1; done
while true; do redis-cli -p 6382 PING && break; sleep 1; done

# Wait for redis to initialize - otherwise CurveManageTopSets.py
# might crash
sleep 10

source /opt/AIL-framework/AILENV/bin/activate
cd /opt/AIL-framework/bin/

# Note: Before adding a script, test if it works and that all
# dependencies are available. Otherwise the whole service will fail.

/opt/AIL-framework/bin/ModuleInformation.py -k 0 -c 1 &
/opt/AIL-framework/bin/Mixer.py &
/opt/AIL-framework/bin/Global.py &
/opt/AIL-framework/bin/Duplicates.py &
/opt/AIL-framework/bin/Attributes.py &
/opt/AIL-framework/bin/Lines.py &
/opt/AIL-framework/bin/DomClassifier.py &
/opt/AIL-framework/bin/Categ.py &
/opt/AIL-framework/bin/Tokenize.py &
/opt/AIL-framework/bin/CreditCards.py &
/opt/AIL-framework/bin/Onion.py &
/opt/AIL-framework/bin/Mail.py &
/opt/AIL-framework/bin/Web.py &
/opt/AIL-framework/bin/Credential.py &
/opt/AIL-framework/bin/Curve.py &

# This crashes if redis isn't ready - execute it in a loop
bash -c "while true; do /opt/AIL-framework/bin/CurveManageTopSets.py; done" &

/opt/AIL-framework/bin/Indexer.py &
/opt/AIL-framework/bin/Keys.py &
/opt/AIL-framework/bin/Phone.py &
/opt/AIL-framework/bin/Release.py &
/opt/AIL-framework/bin/Cve.py &
/opt/AIL-framework/bin/WebStats.py &
/opt/AIL-framework/bin/ModuleStats.py &
/opt/AIL-framework/bin/SQLInjectionDetection.py &
/opt/AIL-framework/bin/alertHandler.py &
/opt/AIL-framework/bin/RegexForTermsFrequency.py &
/opt/AIL-framework/bin/SetForTermsFrequency.py &
/opt/AIL-framework/bin/SentimentAnalysis.py

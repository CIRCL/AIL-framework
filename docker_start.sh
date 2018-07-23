source ./AILENV/bin/activate
cd bin

export PATH=$AIL_HOME:$PATH
export PATH=$AIL_REDIS:$PATH
export PATH=$AIL_LEVELDB:$PATH
export PATH=$AIL_ARDB:$PATH
if [ -z $1 ]; then
    export AILENV=/opt/AIL
  else
    export AILENV=$1
fi

conf_dir="${AIL_HOME}/configs/"

screen -dmS "Redis"
screen -S "Redis" -X screen -t "6379" bash -c 'redis-server '$conf_dir'6379.conf ; read x'
screen -S "Redis" -X screen -t "6380" bash -c 'redis-server '$conf_dir'6380.conf ; read x'
screen -S "Redis" -X screen -t "6381" bash -c 'redis-server '$conf_dir'6381.conf ; read x'

# For Words and curves
sleep 0.1
screen -dmS "ARDB_AIL"
screen -S "ARDB_AIL" -X screen -t "6382" bash -c 'ardb-server '$conf_dir'6382.conf ; read x'

#Want to launch more level_db?
lvdbhost='127.0.0.1'
lvdbdir="${AIL_HOME}/LEVEL_DB_DATA/"
db1_y='2013'
db2_y='2014'
db3_y='2016'
db4_y='2017'

dbC_y='3016'
 
nb_db=13

screen -dmS "LevelDB"
#Add lines here with appropriates options.
screen -S "LevelDB" -X screen -t "2013" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2013/ -P '$db1_y' -M '$nb_db'; read x'
screen -S "LevelDB" -X screen -t "2014" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2014/ -P '$db2_y' -M '$nb_db'; read x'
screen -S "LevelDB" -X screen -t "2016" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2016/ -P '$db3_y' -M '$nb_db'; read x'
screen -S "LevelDB" -X screen -t "2016" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2017/ -P '$db4_y' -M '$nb_db'; read x'

# For Curve
screen -S "LevelDB" -X screen -t "3016" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'3016/ -P '$dbC_y' -M '$nb_db'; read x'


screen -dmS "Logging"
screen -S "Logging" -X screen -t "LogQueue" bash -c 'log_subscriber -p 6380 -c Queuing -l ../logs/; read x'
screen -S "Logging" -X screen -t "LogScript" bash -c 'log_subscriber -p 6380 -c Script -l ../logs/; read x'

screen -dmS "Queue"
screen -S "Queue" -X screen -t "Queues" bash -c './launch_queues.py; read x'

screen -dmS "Script"
screen -S "Script" -X screen -t "ModuleInformation" bash -c './ModuleInformation.py -k 0 -c 1; read x'
screen -S "Script" -X screen -t "Mixer" bash -c './Mixer.py; read x'
screen -S "Script" -X screen -t "Global" bash -c './Global.py; read x'
screen -S "Script" -X screen -t "Duplicates" bash -c './Duplicates.py; read x'
screen -S "Script" -X screen -t "Attributes" bash -c './Attributes.py; read x'
screen -S "Script" -X screen -t "Lines" bash -c './Lines.py; read x'
screen -S "Script" -X screen -t "DomClassifier" bash -c './DomClassifier.py; read x'
screen -S "Script" -X screen -t "Categ" bash -c './Categ.py; read x'
screen -S "Script" -X screen -t "Tokenize" bash -c './Tokenize.py; read x'
screen -S "Script" -X screen -t "CreditCards" bash -c './CreditCards.py; read x'
screen -S "Script" -X screen -t "Onion" bash -c './Onion.py; read x'
screen -S "Script" -X screen -t "Mail" bash -c './Mail.py; read x'
screen -S "Script" -X screen -t "Web" bash -c './Web.py; read x'
screen -S "Script" -X screen -t "Credential" bash -c './Credential.py; read x'
screen -S "Script" -X screen -t "Curve" bash -c './Curve.py; read x'
screen -S "Script" -X screen -t "CurveManageTopSets" bash -c './CurveManageTopSets.py; read x'
screen -S "Script" -X screen -t "Indexer" bash -c './Indexer.py; read x'
screen -S "Script" -X screen -t "Keys" bash -c './Keys.py; read x'
screen -S "Script" -X screen -t "Phone" bash -c './Phone.py; read x'
screen -S "Script" -X screen -t "Release" bash -c './Release.py; read x'
screen -S "Script" -X screen -t "Cve" bash -c './Cve.py; read x'
screen -S "Script" -X screen -t "WebStats" bash -c './WebStats.py; read x'
screen -S "Script" -X screen -t "ModuleStats" bash -c './ModuleStats.py; read x'
screen -S "Script" -X screen -t "SQLInjectionDetection" bash -c './SQLInjectionDetection.py; read x'
screen -S "Script" -X screen -t "BrowseWarningPaste" bash -c './BrowseWarningPaste.py; read x'
screen -S "Script" -X screen -t "SentimentAnalysis" bash -c './SentimentAnalysis.py; read x'

cd $AILENV
cd var/www/
python Flask_server.py

#!/bin/bash

GREEN="\\033[1;32m"
DEFAULT="\\033[0;39m"
RED="\\033[1;31m"
ROSE="\\033[1;35m"
BLUE="\\033[1;34m"
WHITE="\\033[0;02m"
YELLOW="\\033[1;33m"
CYAN="\\033[1;36m"

#Modify these PATH
export PATH=$(pwd):$PATH
export PATH=/opt/redis-2.8.12/src/:$PATH
export PATH=/opt/redis-leveldb/:$PATH

function helptext {
    echo -e $YELLOW"

              .o.            ooooo      ooooo
             .888.           \`888'      \`888'
            .8\"888.           888        888
           .8' \`888.          888        888
          .88ooo8888.         888        888
         .8'     \`888.        888        888       o
        o88o     o8888o   o  o888o   o  o888ooooood8

         Analysis Information Leak framework
    "$DEFAULT"
    This script launch:
    "$CYAN"
    - All the ZMQ queuing modules.
    - All the ZMQ processing modules.
    - All Redis in memory servers.
    - All Level-DB on disk servers.
    "$DEFAULT"
    (Inside screen Daemons)
    "$RED"
    But first of all you'll need to edit few path where you installed
    your redis & leveldb servers.
    "$DEFAULT"
    Usage:
    -----
    "
}

function launching_redis {
    conf_dir='/home/adulau/AIL-framework/configs/'

    screen -dmS "Redis"
    sleep 0.1
    echo -e $GREEN"\t* Launching Redis servers"$DEFAULT
    screen -S "Redis" -X screen -t "6379" bash -c 'redis-server '$conf_dir'6379.conf ; read x'
    sleep 0.1
    screen -S "Redis" -X screen -t "6380" bash -c 'redis-server '$conf_dir'6380.conf ; read x'
    sleep 0.1
    screen -S "Redis" -X screen -t "6381" bash -c 'redis-server '$conf_dir'6381.conf ; read x'
}

function launching_lvldb {
    #Want to launch more level_db?
    lvdbhost='127.0.0.1'
    lvdbdir='/home/adulau//AIL-framework/LEVEL_DB_DATA/'
    db1_y='2013'
    db2_y='2014'
    nb_db=13

    screen -dmS "LevelDB"
    sleep 0.1
    echo -e $GREEN"\t* Launching Levels DB servers"$DEFAULT
    #Add lines here with appropriates options.
    screen -S "LevelDB" -X screen -t "2013" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2013/ -P '$db1_y' -M '$nb_db'; read x'
    sleep 0.1
    screen -S "LevelDB" -X screen -t "2014" bash -c 'redis-leveldb -H '$lvdbhost' -D '$lvdbdir'2014/ -P '$db2_y' -M '$nb_db'; read x'
}

function launching_logs {
    screen -dmS "Logging"
    sleep 0.1
    echo -e $GREEN"\t* Launching logging process"$DEFAULT
    screen -S "Logging" -X screen -t "LogQueue" bash -c './log_subscriber -p 6380 -c Queuing -l ../logs/; read x'
    sleep 0.1
    screen -S "Logging" -X screen -t "LogScript" bash -c './log_subscriber -p 6380 -c Script -l ../logs/; read x'
}

function launching_queues {
    screen -dmS "Queue"
    sleep 0.1

    echo -e $GREEN"\t* Launching redis ZMQ queues"$DEFAULT
    screen -S "Queue" -X screen -t "QFeed" bash -c './ZMQ_Feed_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "QDuplicate" bash -c './ZMQ_Sub_Duplicate_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "QAttributes" bash -c './ZMQ_Sub_Attributes_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "Qlines" bash -c './ZMQ_PubSub_Lines_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "QCateg" bash -c './ZMQ_PubSub_Categ_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "QTokenize" bash -c './ZMQ_PubSub_Tokenize_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "Qcreditcard" bash -c './ZMQ_Sub_CreditCards_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "QOnion" bash -c './ZMQ_Sub_Onion_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "Qmails" bash -c './ZMQ_Sub_Mails_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "Qurls" bash -c './ZMQ_Sub_Urls_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "QCurve" bash -c './ZMQ_Sub_Curve_Q.py; read x'
    sleep 0.1
    screen -S "Queue" -X screen -t "QIndexer" bash -c './ZMQ_Sub_Indexer_Q.py; read x'
}

function launching_scripts {
    screen -dmS "Script"
    sleep 0.1

    echo -e $GREEN"\t* Launching ZMQ scripts"$DEFAULT

    screen -S "Script" -X screen -t "Feed" bash -c './ZMQ_Feed.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Duplicate" bash -c './ZMQ_Sub_Duplicate.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Attributes" bash -c './ZMQ_Sub_Attributes.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Lines" bash -c './ZMQ_PubSub_Lines.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Categ" bash -c './ZMQ_PubSub_Categ.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Tokenize" bash -c './ZMQ_PubSub_Tokenize.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Creditcard" bash -c './ZMQ_Sub_CreditCards.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Onion" bash -c './ZMQ_Sub_Onion.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Mails" bash -c './ZMQ_Sub_Mails.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Urls" bash -c './ZMQ_Sub_Urls.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Curve" bash -c './ZMQ_Sub_Curve.py; read x'
    sleep 0.1
    screen -S "Script" -X screen -t "Indexer" bash -c './ZMQ_Sub_Indexer.py; read x'
}

#If no params, display the help
#[[ $@ ]] || { helptext; exit 1;}

helptext;

############### TESTS ###################
isredis=`screen -ls | awk '/\.Redis\t/ {print strtonum($1)}'`
islvldb=`screen -ls | awk '/\.LevelDB\t/ {print strtonum($1)}'`
islogged=`screen -ls | awk '/\.Logging\t/ {print strtonum($1)}'`
isqueued=`screen -ls | awk '/\.Queue\t/ {print strtonum($1)}'`
isscripted=`screen -ls | awk '/\.Script\t/ {print strtonum($1)}'`

options=("Redis" "LevelDB" "Logs" "Queues" "Scripts" "Killall" "Shutdown")

menu() {
    echo "What do you want to Launch?:"
    for i in ${!options[@]}; do
        printf "%3d%s) %s\n" $((i+1)) "${choices[i]:- }" "${options[i]}"
    done
    [[ "$msg" ]] && echo "$msg"; :
}

prompt="Check an option (again to uncheck, ENTER when done): "
while menu && read -rp "$prompt" num && [[ "$num" ]]; do
    [[ "$num" != *[![:digit:]]* ]] && (( num > 0 && num <= ${#options[@]} )) || {
        msg="Invalid option: $num"; continue
    }
    ((num--)); msg="${options[num]} was ${choices[num]:+un}checked"
    [[ "${choices[num]}" ]] && choices[num]="" || choices[num]="+"
done

for i in ${!options[@]}; do
    if [[ "${choices[i]}" ]]; then
        case ${options[i]} in
            Redis)
                if [[ ! $isredis ]]; then
                    launching_redis;
                else
                    echo -e $RED"\t* A screen is already launched"$DEFAULT
                fi
                ;;
            LevelDB)
                if [[ ! $islvldb ]]; then
                    launching_lvldb;
                else
                    echo -e $RED"\t* A screen is already launched"$DEFAULT
                fi
                ;;
            Logs)
                if [[ ! $islogged ]]; then
                    launching_logs;
                else
                    echo -e $RED"\t* A screen is already launched"$DEFAULT
                fi
                ;;
            Queues)
                if [[ ! $isqueued ]]; then
                    launching_queues;
                else
                    echo -e $RED"\t* A screen is already launched"$DEFAULT
                fi
                ;;
            Scripts)
                if [[ ! $isscripted ]]; then
                    launching_scripts;
                else
                    echo -e $RED"\t* A screen is already launched"$DEFAULT
                fi
                ;;
            Killall)
                if [[ $isredis || $islvldb || $islogged || $isqueued || $isscripted ]]; then
                    kill $isredis $islvldb $islogged $isqueued $isscripted
                    echo -e $ROSE`screen -ls`$DEFAULT
                    echo -e $GREEN"\t* $isredis $islvldb $islogged $isqueued $isscripted killed."$DEFAULT
                else
                    echo -e $RED"\t* No screen to kill"$DEFAULT
                fi
                ;;
            Shutdown)
                bash -c "./Shutdown.py"
                ;;
        esac
    fi
done

#!/bin/bash

GREEN="\\033[1;32m"
DEFAULT="\\033[0;39m"
RED="\\033[1;31m"
ROSE="\\033[1;35m"
BLUE="\\033[1;34m"
WHITE="\\033[0;02m"
YELLOW="\\033[1;33m"
CYAN="\\033[1;36m"

# Getting CWD where bash script resides
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd |sed 's/bin//' )"
export AIL_HOME="${DIR}"

cd ${AIL_HOME}

if [ -e "${DIR}/AILENV/bin/python" ]; then
    ENV_PY="${DIR}/AILENV/bin/python"
    export AIL_VENV=${AIL_HOME}/AILENV/
elif [ ! -z "$TRAVIS" ]; then
    echo "Travis detected"
    ENV_PY="~/virtualenv/python3.6/bin/python"
    export AIL_VENV="~/virtualenv/python3.6/"
else
    echo "Please make sure you have a AIL-framework environment, au revoir"
    exit 1
fi

# redis-server is bundled during install
## [ ! -f "`which redis-server`" ] && echo "'redis-server' is not installed/not on PATH. Please fix and run again." && exit 1

export AIL_BIN=${AIL_HOME}/bin/
export AIL_FLASK=${AIL_HOME}/var/www/
export AIL_REDIS=${AIL_HOME}/redis/src/
export AIL_ARDB=${AIL_HOME}/ardb/src/

export PATH=$AIL_VENV/bin:$PATH
export PATH=$AIL_HOME:$PATH
export PATH=$AIL_REDIS:$PATH
export PATH=$AIL_ARDB:$PATH
export PATH=$AIL_BIN:$PATH
export PATH=$AIL_FLASK:$PATH

isredis=`screen -ls | egrep '[0-9]+.Redis_AIL' | cut -d. -f1`
isardb=`screen -ls | egrep '[0-9]+.ARDB_AIL' | cut -d. -f1`
islogged=`screen -ls | egrep '[0-9]+.Logging_AIL' | cut -d. -f1`
isqueued=`screen -ls | egrep '[0-9]+.Queue_AIL' | cut -d. -f1`
isscripted=`screen -ls | egrep '[0-9]+.Script_AIL' | cut -d. -f1`
isflasked=`screen -ls | egrep '[0-9]+.Flask_AIL' | cut -d. -f1`
iscrawler=`screen -ls | egrep '[0-9]+.Crawler_AIL' | cut -d. -f1`
isfeeded=`screen -ls | egrep '[0-9]+.Feeder_Pystemon' | cut -d. -f1`

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
    - All ARDB on disk servers.
    "$DEFAULT"
    (Inside screen Daemons)
    "$DEFAULT"
    Usage:
    -----
    LAUNCH.sh
      [-l | --launchAuto]
      [-k | --killAll]
      [-u | --update]
      [-c | --configUpdate]
      [-t | --thirdpartyUpdate]
      [-h | --help]
    "
}

function launching_redis {
    conf_dir="${AIL_HOME}/configs/"

    screen -dmS "Redis_AIL"
    sleep 0.1
    echo -e $GREEN"\t* Launching Redis servers"$DEFAULT
    screen -S "Redis_AIL" -X screen -t "6379" bash -c 'redis-server '$conf_dir'6379.conf ; read x'
    sleep 0.1
    screen -S "Redis_AIL" -X screen -t "6380" bash -c 'redis-server '$conf_dir'6380.conf ; read x'
    sleep 0.1
    screen -S "Redis_AIL" -X screen -t "6381" bash -c 'redis-server '$conf_dir'6381.conf ; read x'
}

function launching_ardb {
    conf_dir="${AIL_HOME}/configs/"

    screen -dmS "ARDB_AIL"
    sleep 0.1
    echo -e $GREEN"\t* Launching ARDB servers"$DEFAULT

    sleep 0.1
    screen -S "ARDB_AIL" -X screen -t "6382" bash -c 'cd '${AIL_HOME}'; ardb-server '$conf_dir'6382.conf ; read x'
}

function launching_logs {
    screen -dmS "Logging_AIL"
    sleep 0.1
    echo -e $GREEN"\t* Launching logging process"$DEFAULT
    screen -S "Logging_AIL" -X screen -t "LogQueue" bash -c "cd ${AIL_BIN}; ${AIL_VENV}/bin/log_subscriber -p 6380 -c Queuing -l ../logs/; read x"
    sleep 0.1
    screen -S "Logging_AIL" -X screen -t "LogScript" bash -c "cd ${AIL_BIN}; ${AIL_VENV}/bin/log_subscriber -p 6380 -c Script -l ../logs/; read x"
}

function launching_queues {
    screen -dmS "Queue_AIL"
    sleep 0.1

    echo -e $GREEN"\t* Launching all the queues"$DEFAULT
    screen -S "Queue_AIL" -X screen -t "Queues" bash -c "cd ${AIL_BIN}; ${ENV_PY} launch_queues.py; read x"
}

function checking_configuration {
    bin_dir=${AIL_HOME}/bin
    echo -e "\t* Checking configuration"
    bash -c "${ENV_PY} $bin_dir/Update-conf.py"
    exitStatus=$?
    if [ $exitStatus -ge 1 ]; then
        echo -e $RED"\t* Configuration not up-to-date"$DEFAULT
        exit
    fi
    echo -e $GREEN"\t* Configuration up-to-date"$DEFAULT
}

function launching_scripts {
    checking_configuration;

    screen -dmS "Script_AIL"
    sleep 0.1
    echo -e $GREEN"\t* Launching ZMQ scripts"$DEFAULT

    screen -S "Script_AIL" -X screen -t "ModuleInformation" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./ModulesInformationV2.py -k 0 -c 1; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Mixer" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Mixer.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Global" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Global.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Duplicates" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Duplicates.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Lines" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Lines.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "DomClassifier" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./DomClassifier.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Categ" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Categ.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Tokenize" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Tokenize.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "CreditCards" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./CreditCards.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "BankAccount" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./BankAccount.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Onion" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Onion.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Mail" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Mail.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "ApiKey" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./ApiKey.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Web" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Web.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Credential" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Credential.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Curve" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Curve.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "CurveManageTopSets" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./CurveManageTopSets.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "RegexForTermsFrequency" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./RegexForTermsFrequency.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "SetForTermsFrequency" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./SetForTermsFrequency.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Indexer" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Indexer.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Keys" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Keys.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "PgpDump" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./PgpDump.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Decoder" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Decoder.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Bitcoin" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Bitcoin.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Phone" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Phone.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Release" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Release.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Cve" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Cve.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "WebStats" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./WebStats.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "ModuleStats" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./ModuleStats.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "SQLInjectionDetection" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./SQLInjectionDetection.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "LibInjection" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./LibInjection.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "MISPtheHIVEfeeder" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./MISP_The_Hive_feeder.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Tags" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Tags.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "SentimentAnalysis" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./SentimentAnalysis.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "UpdateBackground" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./update-background.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "SubmitPaste" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./submit_paste.py; read x"

}

function launching_crawler {
    if [[ ! $iscrawler ]]; then
        CONFIG=$AIL_BIN/packages/config.cfg
        lport=$(awk '/^\[Crawler\]/{f=1} f==1&&/^splash_port/{print $3;exit}' "${CONFIG}")

        IFS='-' read -ra PORTS <<< "$lport"
        if [ ${#PORTS[@]} -eq 1 ]
        then
            first_port=${PORTS[0]}
            last_port=${PORTS[0]}
        else
            first_port=${PORTS[0]}
            last_port=${PORTS[1]}
        fi

        screen -dmS "Crawler_AIL"
        sleep 0.1

        for ((i=first_port;i<=last_port;i++)); do
            screen -S "Crawler_AIL" -X screen -t "onion_crawler:$i" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Crawler.py $i; read x"
            sleep 0.1
        done

        echo -e $GREEN"\t* Launching Crawler_AIL scripts"$DEFAULT
    else
        echo -e $RED"\t* A screen is already launched"$DEFAULT
    fi
}

function shutting_down_redis {
    redis_dir=${AIL_HOME}/redis/src/
    bash -c $redis_dir'redis-cli -p 6379 SHUTDOWN'
    sleep 0.1
    bash -c $redis_dir'redis-cli -p 6380 SHUTDOWN'
    sleep 0.1
    bash -c $redis_dir'redis-cli -p 6381 SHUTDOWN'
}

function shutting_down_ardb {
    redis_dir=${AIL_HOME}/redis/src/
    bash -c $redis_dir'redis-cli -p 6382 SHUTDOWN'
}

function checking_redis {
    flag_redis=0
    redis_dir=${AIL_HOME}/redis/src/
    bash -c $redis_dir'redis-cli -p 6379 PING | grep "PONG" &> /dev/null'
    if [ ! $? == 0 ]; then
        echo -e $RED"\t6379 not ready"$DEFAULT
        flag_redis=1
    fi
    sleep 0.1
    bash -c $redis_dir'redis-cli -p 6380 PING | grep "PONG" &> /dev/null'
    if [ ! $? == 0 ]; then
        echo -e $RED"\t6380 not ready"$DEFAULT
        flag_redis=1
    fi
    sleep 0.1
    bash -c $redis_dir'redis-cli -p 6381 PING | grep "PONG" &> /dev/null'
    if [ ! $? == 0 ]; then
        echo -e $RED"\t6381 not ready"$DEFAULT
        flag_redis=1
    fi
    sleep 0.1

    return $flag_redis;
}

function checking_ardb {
    flag_ardb=0
    redis_dir=${AIL_HOME}/redis/src/
    sleep 0.2
    bash -c $redis_dir'redis-cli -p 6382 PING | grep "PONG" &> /dev/null'
    if [ ! $? == 0 ]; then
        echo -e $RED"\t6382 ARDB not ready"$DEFAULT
        flag_ardb=1
    fi

    return $flag_ardb;
}

function wait_until_redis_is_ready {
    redis_not_ready=true
    while $redis_not_ready; do
        if checking_redis; then
            redis_not_ready=false;
        else
            sleep 1
        fi
    done
    echo -e $YELLOW"\t* Redis Launched"$DEFAULT
}

function wait_until_ardb_is_ready {
    ardb_not_ready=true;
    while $ardb_not_ready; do
        if checking_ardb; then
            ardb_not_ready=false
        else
            sleep 3
        fi
    done
    echo -e $YELLOW"\t* ARDB Launched"$DEFAULT
}

function launch_redis {
    if [[ ! $isredis ]]; then
        launching_redis;
    else
        echo -e $RED"\t* A screen is already launched"$DEFAULT
    fi
}

function launch_ardb {
    if [[ ! $isardb ]]; then
        launching_ardb;
    else
        echo -e $RED"\t* A screen is already launched"$DEFAULT
    fi
}

function launch_logs {
    if [[ ! $islogged ]]; then
        launching_logs;
    else
        echo -e $RED"\t* A screen is already launched"$DEFAULT
    fi
}

function launch_queues {
    if [[ ! $isqueued ]]; then
        launching_queues;
    else
        echo -e $RED"\t* A screen is already launched"$DEFAULT
    fi
}

function launch_scripts {
    if [[ ! $isscripted ]]; then
      sleep 1
        if checking_ardb && checking_redis; then
            launching_scripts;
        else
            no_script_launched=true
            while $no_script_launched; do
                echo -e $YELLOW"\tScript not started, waiting 5 more secondes"$DEFAULT
                sleep 5
                if checking_redis && checking_ardb; then
                    launching_scripts;
                    no_script_launched=false
                else
                    echo -e $RED"\tScript not started"$DEFAULT
                fi;
            done
        fi;
    else
        echo -e $RED"\t* A screen is already launched"$DEFAULT
    fi
}

function launch_flask {
    if [[ ! $isflasked ]]; then
        flask_dir=${AIL_FLASK}
        screen -dmS "Flask_AIL"
        sleep 0.1
        echo -e $GREEN"\t* Launching Flask server"$DEFAULT
        screen -S "Flask_AIL" -X screen -t "Flask_server" bash -c "cd $flask_dir; ls; ${ENV_PY} ./Flask_server.py; read x"
    else
        echo -e $RED"\t* A Flask screen is already launched"$DEFAULT
    fi
}

function launch_feeder {
    if [[ ! $isfeeded ]]; then
        screen -dmS "Feeder_Pystemon"
        sleep 0.1
        echo -e $GREEN"\t* Launching Pystemon feeder"$DEFAULT
        screen -S "Feeder_Pystemon" -X screen -t "Pystemon_feeder" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./feeder/pystemon-feeder.py; read x"
        sleep 0.1
        screen -S "Feeder_Pystemon" -X screen -t "Pystemon" bash -c "cd ${AIL_HOME}/../pystemon; ${ENV_PY} ./pystemon.py; read x"
    else
        echo -e $RED"\t* A Feeder screen is already launched"$DEFAULT
    fi
}

function killall {
    if [[ $isredis || $isardb || $islogged || $isqueued || $isscripted || $isflasked || $isfeeded || $iscrawler ]]; then
        if [[ $isredis ]]; then
            echo -e $GREEN"Gracefully closing redis servers"$DEFAULT
            shutting_down_redis;
            sleep 0.2
        fi
        if [[ $isardb ]]; then
            echo -e $GREEN"Gracefully closing ardb servers"$DEFAULT
            shutting_down_ardb;
        fi
        echo -e $GREEN"Killing all"$DEFAULT
        kill $isredis $isardb $islogged $isqueued $isscripted $isflasked $isfeeded $iscrawler
        sleep 0.2
        echo -e $ROSE`screen -ls`$DEFAULT
        echo -e $GREEN"\t* $isredis $isardb $islogged $isqueued $isscripted $isflasked $isfeeded $iscrawler killed."$DEFAULT
    else
        echo -e $RED"\t* No screen to kill"$DEFAULT
    fi
}

function shutdown {
    bash -c "./Shutdown.py"
}

function update() {
    bin_dir=${AIL_HOME}/bin

    bash -c "python3 $bin_dir/Update.py"
    exitStatus=$?
    if [ $exitStatus -ge 1 ]; then
        echo -e $RED"\t* Update Error"$DEFAULT
        exit
    fi
}

function update_thirdparty {
    echo -e "\t* Updating thirdparty..."
    bash -c "(cd ${AIL_FLASK}; ./update_thirdparty.sh)"
    exitStatus=$?
    if [ $exitStatus -ge 1 ]; then
        echo -e $RED"\t* Thirdparty not up-to-date"$DEFAULT
        exit
    else
        echo -e $GREEN"\t* Thirdparty updated"$DEFAULT
    fi
}

function launch_all {
    checking_configuration;
    update;
    launch_redis;
    launch_ardb;
    launch_logs;
    launch_queues;
    launch_scripts;
    launch_flask;
}

#If no params, display the menu
[[ $@ ]] || {

    helptext;

    options=("Redis" "Ardb" "Logs" "Queues" "Scripts" "Flask" "Killall" "Shutdown" "Update" "Update-config" "Update-thirdparty")

    menu() {
        echo "What do you want to Launch?:"
        for i in ${!options[@]}; do
            printf "%3d%s) %s\n" $((i+1)) "${choices[i]:- }" "${options[i]}"
        done
        [[ "$msg" ]] && echo "$msg"; :
    }

    prompt="Check an option (again to uncheck, ENTER when done): "
    while menu && read -rp "$prompt" numinput && [[ "$numinput" ]]; do
        for num in $numinput; do
            [[ "$num" != *[![:digit:]]* ]] && (( num > 0 && num <= ${#options[@]} )) || {
                msg="Invalid option: $num"; break
            }
            ((num--)); msg="${options[num]} was ${choices[num]:+un}checked"
            [[ "${choices[num]}" ]] && choices[num]="" || choices[num]="+"
        done
    done

    for i in ${!options[@]}; do
        if [[ "${choices[i]}" ]]; then
            case ${options[i]} in
                Redis)
                    launch_redis;
                    ;;
                Ardb)
                    launch_ardb;
                    ;;
                Logs)
                    launch_logs;
                    ;;
                Queues)
                    launch_queues;
                    ;;
                Scripts)
                    launch_scripts;
                    ;;
                Flask)
                    launch_flask;
                    ;;
                Crawler)
                    launching_crawler;
                    ;;
                Killall)
                    killall;
                    ;;
                Shutdown)
                    shutdown;
                    ;;
                Update)
                    update;
                    ;;
                Update-config)
                    checking_configuration;
                    ;;
                Update-thirdparty)
                    update_thirdparty;
                    ;;
            esac
        fi
    done

    exit
}

#echo "$@"

while [ "$1" != "" ]; do
    case $1 in
        -l | --launchAuto )           launch_all "automatic";
                                      ;;
        -lr | --launchRedis )         launch_redis;
                                      ;;
        -la | --launchARDB )          launch_ardb;
                                      ;;
        -lrv | --launchRedisVerify )  launch_redis;
                                      wait_until_redis_is_ready;
                                      ;;
        -lav | --launchARDBVerify )   launch_ardb;
                                      wait_until_ardb_is_ready;
                                      ;;
        -k | --killAll )              killall;
                                      ;;
        -u | --update )               update;
                                      ;;
        -t | --thirdpartyUpdate )     update_thirdparty;
                                      ;;
        -c | --crawler )              launching_crawler;
                                      ;;
        -f | --launchFeeder )         launch_feeder;
                                      ;;
        -h | --help )                 helptext;
                                      exit
                                      ;;
        -kh | --khelp )               helptext;

                                      ;;
        * )                           helptext
                                      exit 1
    esac
    shift
done

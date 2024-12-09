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
    . ./AILENV/bin/activate
else
    echo "Please make sure AILENV is installed"
    exit 1
fi

export PATH=$AIL_VENV/bin:$PATH
export PATH=$AIL_HOME:$PATH
export PATH=$AIL_REDIS:$PATH
export PATH=$AIL_KVROCKS:$PATH
export PATH=$AIL_BIN:$PATH
export PATH=$AIL_FLASK:$PATH

function check_screens {
    isredis=`screen -ls | egrep '[0-9]+.Redis_AIL' | cut -d. -f1`
    isardb=`screen -ls | egrep '[0-9]+.ARDB_AIL' | cut -d. -f1`
    iskvrocks=`screen -ls | egrep '[0-9]+.KVROCKS_AIL' | cut -d. -f1`
    islogged=`screen -ls | egrep '[0-9]+.Logging_AIL' | cut -d. -f1`
    is_ail_core=`screen -ls | egrep '[0-9]+.Core_AIL' | cut -d. -f1`
    is_ail_2_ail=`screen -ls | egrep '[0-9]+.AIL_2_AIL' | cut -d. -f1`
    isscripted=`screen -ls | egrep '[0-9]+.Script_AIL' | cut -d. -f1`
    isflasked=`screen -ls | egrep '[0-9]+.Flask_AIL' | cut -d. -f1`
    isfeeded=`screen -ls | egrep '[0-9]+.Feeder_Pystemon' | cut -d. -f1`
}

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
    - All the queuing modules.
    - All the processing modules.
    - All Redis in memory servers.
    - All KVROCKS servers.
    "$DEFAULT"
    (Inside screen Daemons)
    "$DEFAULT"
    Usage:
    -----
    LAUNCH.sh
      [-l  | --launchAuto]         LAUNCH DB + Scripts
      [-k  | --killAll]            Kill DB + Scripts
      [-r  | --restart]            Restart
      [-ks | --killscript]         Scripts
      [-u  | --update]             Update AIL
      [-ut | --thirdpartyUpdate]   Update UI/Frontend
      [-t  | --test]               Launch Tests
      [-rp | --resetPassword]      Reset Password
      [-f  | --launchFeeder]       LAUNCH Pystemon feeder
      [-m  | --menu]               Display Advanced Menu
      [-h  | --help]               Help
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

function launching_kvrocks {
    conf_dir="${AIL_HOME}/configs"

    screen -dmS "KVROCKS_AIL"
    sleep 0.1
    echo -e $GREEN"\t* Launching KVROCKS servers"$DEFAULT

    sleep 0.1
    screen -S "KVROCKS_AIL" -X screen -t "6383" bash -c 'cd '${AIL_HOME}'; ./kvrocks/build/kvrocks -c '$conf_dir'/6383.conf ; read x'
}

function launching_logs {
    conf_dir="${AIL_HOME}/configs/"
    syslog_cmd=""
    syslog_enabled=`cat $conf_dir/core.cfg | grep 'ail_logs_syslog' | cut -d " " -f 3 `
    if [ "$syslog_enabled" = "True" ]; then
      syslog_cmd="--syslog"
    fi
    syslog_server=`cat $conf_dir/core.cfg | grep 'ail_logs_syslog_server' | cut -d " " -f 3 `
    syslog_port=`cat $conf_dir/core.cfg | grep 'ail_logs_syslog_port' | cut -d " " -f 3 `
    if [ ! -z "$syslog_server" -a "$str" != " " ]; then
        syslog_cmd="${syslog_cmd} -ss ${syslog_server}"
        if [ ! -z "$syslog_port" -a "$str" != " " ]; then
            syslog_cmd="${syslog_cmd} -sp ${syslog_port}"
        fi
    fi
    syslog_facility=`cat $conf_dir/core.cfg | grep 'ail_logs_syslog_facility' | cut -d " " -f 3 `
    if [ ! -z "$syslog_facility" -a "$str" != " " ]; then
        syslog_cmd="${syslog_cmd} -sf ${syslog_facility}"
    fi
    syslog_level=`cat $conf_dir/core.cfg | grep 'ail_logs_syslog_level' | cut -d " " -f 3 `
    if [ ! -z "$syslog_level" -a "$str" != " " ]; then
        syslog_cmd="${syslog_cmd} -sl ${syslog_level}"
    fi

    screen -dmS "Logging_AIL"
    sleep 0.1
    echo -e $GREEN"\t* Launching logging process"$DEFAULT
    screen -S "Logging_AIL" -X screen -t "LogScript" bash -c "cd ${AIL_BIN}; ${AIL_VENV}/bin/log_subscriber -p 6380 -c Script -l ../logs/ ${syslog_cmd}; read x"
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

    ##################################
    #         CORE MODULES           #
    ##################################
    # screen -dmS "Core_AIL"
    # sleep 0.1
    echo -e $GREEN"\t* Launching core scripts ..."$DEFAULT

    # Clear Queue Stats
    pushd ${AIL_BIN}
    ${ENV_PY} ./AIL_Init.py
    popd

    # TODO: IMPORTER SCREEN ????
    #### SYNC ####
    screen -S "Script_AIL" -X screen -t "ail_2_ail_server" bash -c "cd ${AIL_BIN}/core; ${ENV_PY} ./ail_2_ail_server.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Sync_importer" bash -c "cd ${AIL_BIN}/core; ${ENV_PY} ./Sync_importer.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Sync_manager" bash -c "cd ${AIL_BIN}/core; ${ENV_PY} ./Sync_manager.py; read x"
    sleep 0.1
    ##-- SYNC --##

    screen -S "Script_AIL" -X screen -t "ZMQImporter" bash -c "cd ${AIL_BIN}/importer; ${ENV_PY} ./ZMQImporter.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "FeederImporter" bash -c "cd ${AIL_BIN}/importer; ${ENV_PY} ./FeederImporter.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "D4_client" bash -c "cd ${AIL_BIN}/core; ${ENV_PY} ./D4_client.py; read x"
    sleep 0.1

    screen -S "Script_AIL" -X screen -t "UpdateBackground" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./update-background.py; read x"
    sleep 0.1

    ##################################
    #           MODULES              #
    ##################################
    # screen -dmS "Script_AIL"
    # sleep 0.1
    echo -e $GREEN"\t* Launching scripts"$DEFAULT

    screen -S "Script_AIL" -X screen -t "Mixer" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Mixer.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Global" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Global.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Categ" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Categ.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Tags" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Tags.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "SubmitPaste" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./SubmitPaste.py; read x"
    sleep 0.1

    screen -S "Script_AIL" -X screen -t "Crawler" bash -c "cd ${AIL_BIN}/crawlers; ${ENV_PY} ./Crawler.py; read x"
    sleep 0.1

    screen -S "Script_AIL" -X screen -t "Sync_module" bash -c "cd ${AIL_BIN}/core; ${ENV_PY} ./Sync_module.py; read x"
    sleep 0.1

    screen -S "Script_AIL" -X screen -t "ApiKey" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./ApiKey.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Credential" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Credential.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "CreditCards" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./CreditCards.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Cryptocurrency" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Cryptocurrencies.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "CveModule" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./CveModule.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Decoder" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Decoder.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Duplicates" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Duplicates.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Iban" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Iban.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "IPAddress" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./IPAddress.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Keys" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Keys.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Languages" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Languages.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Mail" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Mail.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Onion" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Onion.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "PgpDump" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./PgpDump.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Phone" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Phone.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Telegram" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Telegram.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Tools" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Tools.py; read x"
    sleep 0.1

    screen -S "Script_AIL" -X screen -t "Hosts" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Hosts.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "DomClassifier" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./DomClassifier.py; read x"
    sleep 0.1

    screen -S "Script_AIL" -X screen -t "Urls" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Urls.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "SQLInjectionDetection" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./SQLInjectionDetection.py; read x"
    sleep 0.1
#    screen -S "Script_AIL" -X screen -t "LibInjection" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./LibInjection.py; read x"
#    sleep 0.1
#    screen -S "Script_AIL" -X screen -t "Pasties" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Pasties.py; read x"
#    sleep 0.1
#    screen -S "Script_AIL" -X screen -t "Indexer" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Indexer.py; read x"
#    sleep 0.1

    screen -S "Script_AIL" -X screen -t "MISP_Thehive_Auto_Push" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./MISP_Thehive_Auto_Push.py; read x"
    sleep 0.1

    # IMAGES
    screen -S "Script_AIL" -X screen -t "Exif" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./Exif.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "OcrExtractor" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./OcrExtractor.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "CodeReader" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./CodeReader.py; read x"
    sleep 0.1

    # TITLES
    screen -S "Script_AIL" -X screen -t "CEDetector" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./CEDetector.py; read x"
    sleep 0.1

    ##################################
    #       TRACKERS MODULES         #
    ##################################
    screen -S "Script_AIL" -X screen -t "Tracker_Term" bash -c "cd ${AIL_BIN}/trackers; ${ENV_PY} ./Tracker_Term.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Tracker_Typo_Squatting" bash -c "cd ${AIL_BIN}/trackers; ${ENV_PY} ./Tracker_Typo_Squatting.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Tracker_Regex" bash -c "cd ${AIL_BIN}/trackers; ${ENV_PY} ./Tracker_Regex.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Tracker_Yara" bash -c "cd ${AIL_BIN}/trackers; ${ENV_PY} ./Tracker_Yara.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Retro_Hunt" bash -c "cd ${AIL_BIN}/trackers; ${ENV_PY} ./Retro_Hunt.py; read x"
    sleep 0.1
    screen -S "Script_AIL" -X screen -t "Retro_Hunt" bash -c "cd ${AIL_BIN}/trackers; ${ENV_PY} ./Retro_Hunt.py; read x"
    sleep 0.1

    ##################################
    #       DISABLED MODULES         #
    ##################################
    # screen -S "Script_AIL" -X screen -t "SentimentAnalysis" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./SentimentAnalysis.py; read x"
    # sleep 0.1
    # screen -S "Script_AIL" -X screen -t "Release" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./Release.py; read x"
    # sleep 0.1
    # screen -S "Script_AIL" -X screen -t "ModuleStats" bash -c "cd ${AIL_BIN}/modules; ${ENV_PY} ./ModuleStats.py; read x"
    # sleep 0.1

    ##################################
    #          TO MIGRATE            #
    ##################################
#    screen -S "Script_AIL" -X screen -t "ModuleInformation" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./ModulesInformationV2.py -k 0 -c 1; read x"
#    sleep 0.1


}

function shutting_down_redis_servers {
    array=("$@")
    redis_dir=${AIL_HOME}/redis/src
    for port in "${array[@]}";
        do
            bash -c "${redis_dir}/redis-cli -p ${port} -a ail SHUTDOWN"
            sleep 0.1
        done
}

function shutting_down_redis {
    ports=("6379" "6380" "6381")
    shutting_down_redis_servers "${ports[@]}"
}

function shutting_down_ardb {
    ports=("6382")
    shutting_down_redis_servers "${ports[@]}"
}

function shutting_down_kvrocks {
    ports=("6383")
    shutting_down_redis_servers "${ports[@]}"
}

function checking_redis_servers {
    db_name=$1
    shift
    array=("$@")
    redis_dir="${AIL_HOME}/redis/src"
    flag_db=0
    for port in "${array[@]}";
        do
            sleep 0.2
            bash -c "${redis_dir}/redis-cli -p ${port} -a ail PING | grep "PONG" &> /dev/null"
            if [ ! $? == 0 ]; then
                echo -e "${RED}\t${port} ${db_name} not ready${DEFAULT}"
                flag_db=1
            fi
        done
    return $flag_db;
}

function checking_redis {
    ports=("6379" "6380" "6381")
    checking_redis_servers "Redis" "${ports[@]}"
    return $?
}

function checking_ardb {
    ports=("6382")
    checking_redis_servers "ARDB" "${ports[@]}"
    return $?
}

function checking_kvrocks {
    ports=("6383")
    checking_redis_servers "KVROCKS" "${ports[@]}"
    return $?
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

function wait_until_kvrocks_is_ready {
    not_ready=true;
    while $not_ready; do
        if checking_kvrocks; then
            not_ready=false
        else
            sleep 3
        fi
    done
    echo -e $YELLOW"\t* KVROCKS Launched"$DEFAULT
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

function launch_kvrocks {
    if [[ ! $iskvrocks ]]; then
        launching_kvrocks;
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

function launch_scripts {
    if [[ ! $isscripted ]]; then ############################# is core
      sleep 1
        if checking_redis && checking_kvrocks; then
            launching_scripts;
        else
            no_script_launched=true
            while $no_script_launched; do
                echo -e $YELLOW"\tScript not started, waiting 5 more secondes"$DEFAULT
                sleep 5
                if checking_redis && checking_kvrocks; then
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
        screen -S "Feeder_Pystemon" -X screen -t "Pystemon_feeder" bash -c "cd ${AIL_BIN}; ${ENV_PY} ./importer/PystemonImporter.py; read x"
        sleep 0.1
        screen -S "Feeder_Pystemon" -X screen -t "Pystemon" bash -c "cd ${AIL_HOME}/../pystemon; ${ENV_PY} ./pystemon.py; read x"
    else
        echo -e $RED"\t* A Feeder screen is already launched"$DEFAULT
    fi
}

function killscript {
    if [[ $islogged || $is_ail_core || $isscripted || $isflasked || $isfeeded || $is_ail_2_ail ]]; then
        echo -e $GREEN"Killing Script"$DEFAULT
        kill $islogged $is_ail_core $isscripted $isflasked $isfeeded $is_ail_2_ail
        sleep 0.2
        echo -e $ROSE`screen -ls`$DEFAULT
        echo -e $GREEN"\t* $islogged $is_ail_core $isscripted $isflasked $isfeeded $is_ail_2_ail killed."$DEFAULT
    else
        echo -e $RED"\t* No script to kill"$DEFAULT
    fi
}

function killall {
    if [[ $isredis || $isardb || $iskvrocks || $islogged || $is_ail_2_ail || $isscripted || $isflasked || $isfeeded || $is_ail_core || $is_ail_2_ail ]]; then
        if [[ $isredis ]]; then
            echo -e $GREEN"Gracefully closing redis servers"$DEFAULT
            shutting_down_redis;
            sleep 0.2
        fi
        if [[ $isardb ]]; then
            echo -e $GREEN"Gracefully closing ardb servers"$DEFAULT
            shutting_down_ardb;
        fi
        if [[ $iskvrocks ]]; then
            echo -e $GREEN"Gracefully closing Kvrocks servers"$DEFAULT
            shutting_down_kvrocks;
        fi
        echo -e $GREEN"Killing all"$DEFAULT
        kill $isredis $isardb $iskvrocks $islogged $is_ail_core $isscripted $isflasked $isfeeded $is_ail_2_ail
        sleep 0.2
        echo -e $ROSE`screen -ls`$DEFAULT
        echo -e $GREEN"\t* $isredis $isardb $iskvrocks $islogged $isscripted $is_ail_2_ail $isflasked $isfeeded $is_ail_core killed."$DEFAULT
    else
        echo -e $RED"\t* No screen to kill"$DEFAULT
    fi
}

function _set_kvrocks_namespace() {
  bash -c "${redis_dir}/redis-cli -p ${port} -a ail namespace add $1 $2"
}

function set_kvrocks_namespaces() {
  if checking_kvrocks; then
    _set_kvrocks_namespace "cor"  "ail_correls"
    _set_kvrocks_namespace "obj"  "ail_objs"
    _set_kvrocks_namespace "tag"  "ail_tags"
  else
    echo -e $RED"\t* Error: Please launch Kvrocks server"$DEFAULT
  fi
}

function update() {
    bin_dir=${AIL_HOME}/bin

    bash -c "python3 $bin_dir/Update.py $1"
    exitStatus=$?
    if [ $exitStatus -ge 3 ]; then
        echo -e "\t* Update..."
        bash -c "python3 $bin_dir/Update.py $1"
        exitStatus=$?
        if [ $exitStatus -ge 1 ]; then
            echo -e $RED"\t* Update Error"$DEFAULT
            exit
        fi
    fi

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

function launch_tests() {
  tests_dir=${AIL_HOME}/tests
  bin_dir=${AIL_BIN}
  echo -e ""
  echo -e $GREEN"AIL SCREENS:"$DEFAULT
  echo -e $ROSE`screen -ls`$DEFAULT
  echo -e $GREEN"\t* Redis:   $isredis"$DEFAULT
  echo -e $GREEN"\t* Kvrocks: $iskvrocks $isscripted $isflasked"$DEFAULT
  echo -e $GREEN"\t* Modules: $isscripted"$DEFAULT
  echo -e $GREEN"\t* Flask:   $isflasked"$DEFAULT
  echo -e ""
  echo -e ""
  python3 -m nose2 --start-dir $tests_dir --coverage $bin_dir --with-coverage test_api test_modules
}

function reset_password() {
  echo -e "\t* Resetting UI admin password..."
  if checking_kvrocks && checking_redis; then
      python ${AIL_HOME}/var/www/create_default_user.py &
      wait
  else
      echo -e $RED"\t* Error: Please launch all Redis and ARDB servers"$DEFAULT
      exit
  fi
}

function launch_all {
    checking_configuration;
    update;
    launch_redis;
    launch_kvrocks;
    launch_scripts;
    launch_flask;
}

function menu_display {

  options=("Redis" "Kvrocks" "Scripts" "Flask" "Killall" "Update" "Update-config" "Update-thirdparty")

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
              Kvrocks)
                  launch_kvrocks;
                  ;;
              Scripts)
                  launch_scripts;
                  ;;
              Flask)
                  launch_flask;
                  ;;
              Killall)
                  killall;
                  ;;
              Update)
                  checking_configuration;
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


#If no params, display the help
[[ $@ ]] || {

    helptext;
}

#echo "$@"
check_screens;
while [ "$1" != "" ]; do
    case $1 in
        -l | --launchAuto )             check_screens;
                                        launch_all "automatic";
                                        ;;
        -lr | --launchRedis )           check_screens;
                                        launch_redis;
                                        ;;
        -la | --launchARDB )            launch_ardb;
                                        ;;
        -lk | --launchKVROCKS )         check_screens;
                                        launch_kvrocks;
                                        ;;
        -lrv | --launchRedisVerify )    launch_redis;
                                        wait_until_redis_is_ready;
                                        ;;
        -lkv | --launchKVORCKSVerify )  launch_kvrocks;
                                        wait_until_kvrocks_is_ready;
                                        ;;
        --set_kvrocks_namespaces )      set_kvrocks_namespaces;
                                        ;;
        -k | --killAll )                check_screens;
                                        killall;
                                        ;;
        -r | --restart )                killall;
                                        sleep 0.1;
                                        check_screens;
                                        launch_all "automatic";
                                        ;;
        -ks | --killscript )            check_screens;
                                        killscript;
                                        ;;
        -m | --menu )                   menu_display;
                                        ;;
        -u | --update )                 checking_configuration;
                                        update "--manual";
                                        ;;
        -t | --test )                   launch_tests;
                                        ;;
        -ut | --thirdpartyUpdate )      update_thirdparty;
                                        ;;
        -rp | --resetPassword )         reset_password;
                                        ;;
        -f | --launchFeeder )           launch_feeder;
                                        ;;
        -h | --help )                   helptext;
                                        exit
                                        ;;
        -kh | --khelp )                 helptext;
                                        ;;
        * )                             helptext
                                        exit 1
    esac
    shift
done

#!/bin/bash

RED="\\033[1;31m"
DEFAULT="\\033[0;39m"
GREEN="\\033[1;32m"

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;

function helptext {
    echo -e $GREEN"

              .o.            ooooo      ooooo
             .888.           \`888'      \`888'
            .8\"888.           888        888
           .8' \`888.          888        888
          .88ooo8888.         888        888
         .8'     \`888.        888        888       o
        o88o     o8888o   o  o888o   o  o888ooooood8

         Analysis Information Leak framework
    "$DEFAULT"
    Use this script to reset AIL (DB + stored items):

    Usage:
    -----
    reset_AIL.sh
      [--softReset]               Keep All users accounts
      [-h  | --help]              Help
    "
}

function reset_dir {
  # Access dirs and delete
  cd $AIL_HOME

  # Kill all screens
  screen -ls | grep Detached | cut -d. -f1 | awk '{print $1}' | xargs kill

  # Access dirs and delete
  cd $AIL_HOME

  if [ -d indexdir/ ]; then
    pushd indexdir/
    rm -r *
    echo 'cleaned indexdir'
    popd
  fi

  if [ -d logs/ ]; then
    pushd logs/
    rm *
    echo 'cleaned logs'
    popd
  fi

  if [ -d PASTES/ ]; then
    pushd PASTES/
    rm -r *
    echo 'cleaned PASTES'
    popd
  fi

  if [ -d HASHS/ ]; then
    pushd HASHS/
    rm -r *
    echo 'cleaned HASHS'
    popd
  fi

  if [ -d CRAWLED_SCREESHOT/ ]; then
    pushd CRAWLED_SCREESHOT/
    rm -r *
    echo 'cleaned CRAWLED_SCREESHOT'
    popd
  fi

  if [ -d temp/ ]; then
    pushd temp/
    rm -r *
    echo 'cleaned temp'
    popd
  fi

  if [ -d var/www/submitted/ ]; then
    pushd var/www/submitted
    rm -r *
    echo 'cleaned submitted'
    popd
  fi

  echo -e $GREEN"* AIL has been reset *"$DEFAULT
}

function flush_DB_keep_user {
  bash ${AIL_BIN}LAUNCH.sh -lav &
  wait
  echo ""
  pushd redis/src
    ./redis-cli -p 6382 -n 1 FLUSHDB;
    ./redis-cli -p 6382 -n 2 FLUSHDB;
    ./redis-cli -p 6382 -n 3 FLUSHDB;
    ./redis-cli -p 6382 -n 4 FLUSHDB;
    ./redis-cli -p 6382 -n 5 FLUSHDB;
    ./redis-cli -p 6382 -n 6 FLUSHDB;
    ./redis-cli -p 6382 -n 7 FLUSHDB;
    ./redis-cli -p 6382 -n 8 FLUSHDB;
    ./redis-cli -p 6382 -n 9 FLUSHDB;
    echo "ARDB FLUSHED"
  popd
  bash ${AIL_BIN}LAUNCH.sh -k
}

function validate_reset {
  echo -e $RED"WARNING: DELETE AIL DATA"$DEFAULT

  # Make sure the reseting is intentional
  num=$(( ( RANDOM % 100 )  + 1 ))

  echo -e $RED"To reset the platform, enter the following number: "$DEFAULT $num
  read userInput

  if [ $userInput -eq $num ]
  then
      echo "Reseting AIL..."
  else
      echo "Wrong number"
      exit 1;
  fi
}

function soft_reset {
  validate_reset;
  reset_dir;
  flush_DB_keep_user;
}

#If no params,
[[ $@ ]] || {
    validate_reset;

    num=$(( ( RANDOM % 100 )  + 1 ))
    echo -e $RED"If you want to delete the DB , enter the following number: "$DEFAULT $num
    read userInput

    reset_dir;

    if [ $userInput -eq $num ]
    then
      if [ -d DATA_ARDB/ ]; then
        pushd DATA_ARDB/
        rm -r *
        echo 'cleaned DATA_ARDB'
        popd
      fi
    fi

    echo -e $GREEN"* AIL has been reset *"$DEFAULT

    exit
}

while [ "$1" != "" ]; do
    case $1 in
        --softReset )           soft_reset;
                                ;;
        -h | --help )           helptext;
                                exit
                                ;;
        * )                     exit 1
    esac
    shift
done

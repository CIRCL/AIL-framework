#!/bin/bash

RED="\\033[1;31m"
DEFAULT="\\033[0;39m"
GREEN="\\033[1;32m"

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;

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

  if [ $userInput -eq $num ]
  then
    if [ -d DATA_ARDB/ ]; then
      pushd DATA_ARDB/
      rm -r *
      echo 'cleaned DATA_ARDB'
      popd
    fi
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

  exit
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
  popd
  bash ${AIL_BIN}LAUNCH.sh -k
}

function soft_reset {
  reset_dir;
  flush_DB_keep_user;
}

#If no params,
[[ $@ ]] || {
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

    num=$(( ( RANDOM % 100 )  + 1 ))
    echo -e $RED"If yes you want to delete the DB , enter the following number: "$DEFAULT $num
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
        * )                     exit 1
    esac
    shift
done

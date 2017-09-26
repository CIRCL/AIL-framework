#!/bin/bash

RED="\\033[1;31m"
DEFAULT="\\033[0;39m"
GREEN="\\033[1;32m"

[ -z "$AIL_HOME" ] && echo "Needs the env var AIL_HOME. Run the script from the virtual environment." && exit 1;

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


# Kill all screens
screen -ls | grep Detached | cut -d. -f1 | awk '{print $1}' | xargs kill

set -e

# Access dirs and delete
cd $AIL_HOME

pushd dumps/
rm *
echo 'cleaned dumps'
popd

pushd indexdir/
rm -r *
echo 'cleaned indexdir'
popd

pushd LEVEL_DB_DATA/
rm -r *
echo 'cleaned LEVEL_DB_DATA'
popd

pushd logs/
rm *
echo 'cleaned logs'
popd

pushd PASTES/
rm -r *
echo 'cleaned PASTES'
popd

echo -e $GREEN"* AIL has been reset *"$DEFAULT

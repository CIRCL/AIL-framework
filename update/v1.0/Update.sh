#!/bin/bash
YELLOW="\\033[1;33m"
DEFAULT="\\033[0;39m"

echo -e $YELLOW"\t"
echo -e "* ------------------------------------------------------------------"
echo -e "\t"
echo -e " - - - - - - - -        PLEASE RELAUNCH AIL   - - - - - - - -  "
echo -e "\t"
echo -e "* ------------------------------------------------------------------"
echo -e "\t"
echo -e "\t"$DEFAULT

# fix invalid Updater version (kill parent):
kill -SIGUSR1 `ps --pid $$ -oppid=`; exit

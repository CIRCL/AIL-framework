#!/bin/bash

# fix invalid Updater version (kill parent):
kill -SIGUSR1 `ps --pid $$ -oppid=`; exit

#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import time

sys.path.append(os.environ['AIL_BIN'])
##################################
# Import Project packages
##################################
from core import ail_2_ail

# # TODO: launch me in core screen

if __name__ == '__main__':

    Client_Manager = ail_2_ail.AIL2AILClientManager()

    while True:
        command = Client_Manager.get_manager_command()
        if command:
            Client_Manager.execute_manager_command(command)
        else:
            time.sleep(5)

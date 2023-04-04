#!/usr/bin/env python3
# -*-coding:UTF-8 -*

# import os
# import sys
# import uuid
#
# sys.path.append(os.environ['AIL_BIN'])
# ##################################
# # Import Project packages
# ##################################
# from lib.ConfigLoader import ConfigLoader

## LOAD CONFIG ##
# config_loader = ConfigLoader()
#
# r_serv_metadata = config_loader.get_redis_conn("ARDB_Metadata")  ######################################
# config_loader = None
## -- ##

# sys.path.append('../../configs/keys')
##################################
# Import Keys
##################################
from thehive4py.api import TheHiveApi
from thehive4py.models import Alert, AlertArtifact, Case, CaseObservable
import thehive4py.exceptions

from pymisp import MISPEvent, MISPObject, PyMISP

###########################################################
# # set default
# if r_serv_db.get('hive:auto-alerts') is None:
#     r_serv_db.set('hive:auto-alerts', 0)
#
# if r_serv_db.get('misp:auto-events') is None:
#     r_serv_db.set('misp:auto-events', 0)

# if __name__ == '__main__':
# from lib.objects.Cves import Cve
# create_misp_event([Item('crawled/2020/09/14/circl.lu0f4976a4-dda4-4189-ba11-6618c4a8c951'),
#                       Cve('CVE-2020-16856'), Cve('CVE-2014-6585'), Cve('CVE-2015-0383'),
#                       Cve('CVE-2015-0410')])

# create_investigation_misp_event('c6bbf8fa9ead4cc698eaeb07835cca5d)

#!/bin/bash

source /opt/AIL-framework/AILENV/bin/activate
/bin/mkdir -p /var/log/AIL
/bin/bash -c "/usr/local/bin/log_subscriber -p 6380 -c Queuing -l /var/log/AIL&"
/usr/local/bin/log_subscriber -p 6380 -c Script -l /var/log/AIL

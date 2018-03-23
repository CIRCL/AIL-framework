#!/bin/bash

cd /opt/AIL-framework/configs && \
/bin/bash -c "/usr/bin/redis-server /opt/AIL-framework/configs/6379.conf &" && \
/bin/bash -c "/usr/bin/redis-server  /opt/AIL-framework/configs/6380.conf &" && \
/bin/bash -c "/usr/bin/redis-server /opt/AIL-framework/configs/6381.conf &" && \
/bin/bash -c "/usr/bin/redis-server /opt/AIL-framework/configs/6382.conf"

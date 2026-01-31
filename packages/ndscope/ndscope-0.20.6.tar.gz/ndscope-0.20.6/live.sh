#!/bin/bash

#python3 -m ndscope --trend raw -t 1426700000 -t 1426700030 H1:GDS-CALIB_STRAIN
export NDSSERVER=localhost:8088
export LOG_LEVEL=DEBUG
python3 -m ndscope live.yaml
#!/bin/bash

#python3 -m ndscope --trend raw -t 1426700000 -t 1426700030 H1:GDS-CALIB_STRAIN
export LIGO_DATA_URL=nds://localhost:8089
python3 -m ndscope live.yaml
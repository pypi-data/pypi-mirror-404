#!/bin/bash

export LIGO_DATA_URL=grpc://localhost:31206
#python3 -m ndscope --trend raw -t 1426700000 -t 1426700030 H1:GDS-CALIB_STRAIN
python3 -m ndscope calib_arrakis.yaml
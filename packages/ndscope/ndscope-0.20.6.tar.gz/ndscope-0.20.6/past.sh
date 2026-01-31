#!/bin/bash

#export NDSSERVER=nds.ligo-wa.caltech.edu:31200
export NDSSERVER=localhost:8088
#python3 -m ndscope --trend raw -t 1426700000 -t 1426700030 H1:GDS-CALIB_STRAIN
python3 -m ndscope past2.yaml

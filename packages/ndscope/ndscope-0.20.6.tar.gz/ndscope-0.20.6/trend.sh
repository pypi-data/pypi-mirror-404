#!/bin/bash

export NDSSERVER=nds.ligo.caltech.edu:31200
#python3 -m ndscope --trend raw -t 1426700000 -t 1426700030 H1:GDS-CALIB_STRAIN
python3 -m ndscope trend.yaml
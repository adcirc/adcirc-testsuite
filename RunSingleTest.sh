#!/bin/bash

#...Maximum Error
err=0.00001

#...Path to the executables
adcirc_path=$1

#...Path to case
case=$2

#...Current home location
TESTHOME=$(pwd)

#...Run the test using python
python3 $TESTHOME/test_runner/test_runner.py \
    --bin $adcirc_path \
    --tolerance $err \
    --test-root $TESTHOME \
    --test-yaml $TESTHOME/test_list.yaml \
    --test $case
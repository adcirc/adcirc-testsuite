#!/bin/bash

#...Maximum Error
err=0.00001

#...Path to the executables
adcirc_path=$1

#...Path to case
case=$2

#...Current home location
TESTHOME=$(pwd)

cont=0
if [ $# -eq 3 ] ; then
    if [ $2 == "--continue" ] ; then
        cont=1
    fi
fi
#
#...Sanity check on script arguments
if [ $# -ne 1 ] && [ $# -ne 2 ] && [ $# -ne 3 ] ; then
    echo "ERROR: Script requires 2 arguments with folder containing executables and path to case which will be run."
    exit 1
fi

#...Ensure that a relative path is not supplied
if [ "x${adcirc_path:0:1}" != "x/" ] ; then
    echo "ERROR: You must provide an absoloute path."
    exit 1
fi

#...Check if case directory exists with run script
if [ ! -s $case/run.sh ] ; then
    echo "ERROR: Case directory does not exist or does not contain run.sh"
    exit 1
fi

#...Check if adcirc exists
if [ ! -s $1/adcirc ] ; then
    echo "ERROR: adcirc executable not found."
    exit 1
fi

#...Check if adcprep exists
if [ ! -s $1/adcprep ] ; then
    echo "ERROR: adcprep executable not found."
    exit 1
fi

#...Check if padcirc exists
if [ ! -s $1/padcirc ] ; then
    echo "ERROR: padcirc executable not found."
    exit 1
fi

#...Check of adccmp exists
if [ ! -s $1/adcircResultsComparison ] ; then
    echo "ERROR: adcircResultsComparison executable not found."
    exit 1
fi

#...Check if adcswan exists
if [ ! -s $1/adcswan ] ; then
    echo "ERROR: adcswan executable not found."
    exit 1
fi

#...Check if padcswan exists
if [ ! -s $1/padcswan ] ; then
    echo "ERROR: padcswan executable not found."
    exit 1
fi

#...Proceed into the case directory
cd $case

#...Check for the generic run.sh script
if [ ! -s run.sh ]; then
    echo "ERROR: Could not find run script for $CASE"
    exit 1
fi

#...Run the case and check the return status
./run.sh $adcirc_path $err 2>/dev/null
if [ $? -ne 0 ] ; then
    echo "ERROR: The case $CASE did not pass."
    if [ $cont == 0 ] ; then
        exit 1
    fi
fi


#...Exit with status zero if all tests have passed
exit 0

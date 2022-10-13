#!/bin/bash

#...List of ADCIRC's test cases. Cases are named by their directory tree
case_list=( adcirc/adcirc_apes                                       \
            adcirc/adcirc_quarterannular-2d                          \
            adcirc/adcirc_shinnecock_inlet                           \
            adcirc/adcirc_rivers                                     \
            adcirc/adcirc_internal_overflow                          \
            adcirc/adcirc_nws30_wlcorrection                         \
            adcirc/adcirc_katrina-2d                                 \
            adcirc/adcirc_global-tide-2d                             \
            adcirc/adcirc_global_nws10-2d                            \
            adcirc/adcirc_global-tide+surge-2d                       \
            adcirc/adcirc_apes-parallel                              \
            adcirc/adcirc_internal_overflow-parallel                 \
            adcirc/adcirc_rivers-parallel                            \
            adcirc/adcirc_quarterannular-2d-netcdf                   \
            adcirc/adcirc_quarterannular-2d-parallel                 \
            adcirc/adcirc_quarterannular-2d-parallel-netcdf          \
            adcirc/adcirc_quarterannular-2d-parallel-netcdf-writer   \
            adcirc/adcirc_quarterannular-2d-parallel-writer          \
            adcirc/adcirc_quarterannular-2d-hotstart                 \
            adcirc/adcirc_quarterannular-2d-netcdf-hotstart          \
            adcirc/adcirc_quarterannular-2d-parallel-hotstart        \
            adcirc/adcirc_quarterannular-2d-parallel-netcdf-hotstart \
            adcirc/adcirc_shinnecock_inlet-parallel                  \
            adcirc/adcirc_nws30_wlcorrection-parallel                \
            adcirc/adcirc_katrina-2d-parallel                        \
            adcirc/adcirc_katrina-2d-nws13                           \
            adcirc/adcirc_katrina-2d-nws13-parallel                  \
            adcirc/adcirc_ideal_channel-2d-parallel                  \
            adcirc/adcirc_ideal_channel-woffset-2d-parallel          \
            adcirc/adcirc_global-alidisp+buoyancy-2d-parallel        \
            adcirc/adcirc_alaska_ice-2d                              \
            adcirc/adcirc_timevaryingweirs-parallel                  \
	    adcirc/adcirc_shinnecock_inlet-parallel                  \)
            adcirc/adcirc_slopingbeach_vew1d-parallel                )
# @jasonfleming 20181206 : FIXME : adcirc+swan tests failing for unknown reasons
#            adcirc-swan/adcirc_swan_apes_irene                       \
#            adcirc-swan/adcirc_swan_apes_irene-parallel              )

#...Maximum Error
err=0.00001

#...Path to the executables
adcirc_path=$1

#...Current home location
TESTHOME=$(pwd)

cont=0
if [ $# -eq 2 ] ; then
    if [ $2 == "--continue" ] ; then
        cont=1
    fi
fi
#
#...Sanity check on script arguments
if [ $# -ne 1 ] && [ $# -ne 2 ]  ; then
    echo "ERROR: Script requires 1 argument with folder containing executables."
    exit 1
fi

#...Ensure that a relative path is not supplied
if [ "x${adcirc_path:0:1}" != "x/" ] ; then
    echo "ERROR: You must provide an absoloute path."
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

#...Loop to run over all the test cases
for CASE in ${case_list[@]}
do

    #...Proceed into the case directory
    cd $CASE

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

    #...Back to testing home location
    cd $TESTHOME
done

#...Exit with status zero if all tests have passed
exit 0

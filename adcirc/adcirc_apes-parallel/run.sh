#!/bin/bash

case_name="adcirc_apes-parallel"

#...Check on what is provided
if [ $# -ne 3 ] ; then
    echo "ERROR: Script requires 3 arguments!"
    echo "    Argument 1: Folder containing adcirc and adccmp executables."
    echo "    Argument 2: Maximum absoloute error"
    echo "    Argument 3: Maximum relative error"
    echo "Exiting with status 1, Failed."
    exit 1
fi

#...Set variables
exepath=$1
abserr=$2
relerr=$3

#...Run the case
echo ""
echo "|---------------------------------------------|"
echo "    TEST CASE: $case_name"
echo ""
echo -n "    Prepping case..."
$exepath/adcprep --np 2 --partmesh >  adcprep.log
$exepath/adcprep --np 2 --prepall  >> adcprep.log
echo "done!"
echo -n "    Runnning case..."
mpirun -np 2 $exepath/padcirc > padcirc_log.txt
exitstat=$?
echo "Finished"
echo "    PADCIRC Exit Code: $exitstat"
if [ "x$exitstat" != "x0" ] ; then
    echo "    ERROR: PADCIRC did not exit cleanly."
    exit 1
fi
echo ""

#...Run the comparison test
echo -n "    Running comparison..."
$exepath/adccmp control . ETA2 $abserr $relerr > wse_comparison.log
$exepath/adccmp control . VV2  $abserr $relerr > vel_comparison.log
$exepath/adccmp control . RMU00 $abserr $relerr > win_comparison.log
$exepath/adccmp control . PR2  $abserr $relerr > pre_comparison.log
nerror_wse=$(cat wse_comparison.log | grep failed | wc -l)
nerror_vel=$(cat vel_comparison.log | grep failed | wc -l)
nerror_win=$(cat win_comparison.log | grep failed | wc -l)
nerror_pre=$(cat pre_comparison.log | grep failed | wc -l)
echo "Finished"

#...Check the number of failed steps
if [ "x$nerror_wse" == "x0" -a "x$nerror_vel" == "x0" -a "x$nerror_win" == "x0" -a "x$nerror_pre" == "x0" ] ; then
    echo "    Test $case_name Passed!"
    echo "|---------------------------------------------|"
    echo ""
    exit 0
else
    echo "    ERROR: Test $case_name Failed!"
    echo ""
    echo "    ERROR Summary"
    echo "      WSE Errors: $nerror_wse"
    echo "      VEL Errors: $nerror_vel"
    echo "      WIN Errors: $nerror_win"
    echo "      PRE Errors: $nerror_pre"
    echo "|---------------------------------------------|"
    echo ""
    exit 1
fi

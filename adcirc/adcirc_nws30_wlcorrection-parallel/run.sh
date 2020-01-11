#!/bin/bash

case_name="aadcirc_nws30_wlcorrection-parallel"

#...Check on what is provided
if [ $# -ne 2 ] ; then
    echo "ERROR: Script requires 3 arguments!"
    echo "    Argument 1: Folder containing adcirc and adccmp executables."
    echo "    Argument 2: Maximum error"
    echo "Exiting with status 1, Failed."
    exit 1
fi

#...Set variables
exepath=$1
err=$2
np=3

nfiles=13
files=( "dynamicWaterlevelCorrection.61.nc"  "dynamicWaterlevelCorrection.63.nc"  "fort.61"  "fort.63"  "fort.62"  "fort.64"  "fort.71.nc"  "fort.72.nc"  "fort.73.nc"  "fort.74.nc"  "maxele.63"  "maxvel.63"  "maxwvel.63.nc"  "minpr.63.nc" )

#...Run the case
echo ""
echo "|---------------------------------------------|"
echo "    TEST CASE: $case_name"
echo ""
echo -n "    Prepping case..."
$exepath/adcprep --np $np --partmesh >  adcprep.log
$exepath/adcprep --np $np --prepall  >> adcprep.log
if [ $? == 0 ] ; then
    echo "done!"
else
    echo "ERROR!"
    exit 1
fi

echo -n "    Runnning case..."
mpirun --allow-run-as-root -np $np $exepath/padcirc > padcirc_log.txt
exitstat=$?
echo "Finished"
echo "    ADCIRC Exit Code: $exitstat"
if [ "x$exitstat" != "x0" ] ; then
    echo "    ERROR: ADCIRC did not exit cleanly."
    exit 1
fi
echo ""


#...Run the comparison test
echo -n "    Running comparison..."
for((i=0;i<$nfiles;i++))
do
    echo "" >> comparison.log
    echo "${files[$i]}" >> comparison.log
    CLOPTIONS="-t $err"    
    if [[ ${files[$i]} = "maxvel.63.nc" || ${files[$i]} = "maxele.63.nc" || ${files[$i]} = "maxwvel.63.nc" || ${files[$i]} = "minpr.63.nc" ]]; then
       CLOPTIONS="$CLOPTIONS --minmax"
    fi            
    $exepath/adcircResultsComparison $CLOPTIONS -f1 ${files[$i]} -f2 control/${files[$i]} >> comparison.log 2>>comparison.log
    error[$i]=$?
done
echo "Finished"

#...Check the number of failed steps
fail=0
for((i=0;i<$nfiles;i++))
do
    echo -n "      "${files[$i]}": "
    if [ "x${error[$i]}" != "x0" ] ; then
        echo "Failed"
        fail=1
    else
        echo "Passed"
    fi
done

if [ $fail == 1 ] ; then
    echo "    Comparison Failed!"
else
    echo "    Comparison Passed!"
fi

echo "|---------------------------------------------|"
echo ""

if [ $fail == 1 ] ; then
    exit 1
else
    exit 0
fi
#!/bin/bash

case_name="adcirc_global_nws10-2d"

#...Check on what is provided
if [ $# -ne 2 ] ; then
    echo "ERROR: Script requires 2 arguments!"
    echo "    Argument 1: Folder containing adcirc and adccmp executables."
    echo "    Argument 2: Maximum error"
    echo "Exiting with status 1, Failed."
    exit 1
fi

#...Set variables
exepath=$1
err=$2
np=3

nfiles=8
files=( "fort.63.nc" "fort.64.nc" "maxele.63.nc" "maxvel.63.nc" "fort.73.nc" "fort.74.nc" "maxwvel.63.nc" "minpr.63.nc" "windDrag.173.nc" )

#...Run the case
echo ""
echo "|---------------------------------------------|"
echo "    TEST CASE: $case_name"
echo ""
cd 01_cs

echo -n "    Prepping case..."
$exepath/adcprep --np $np --partmesh >  adcprep.log
$exepath/adcprep --np $np --prepall  >> adcprep.log
if [ $? == 0 ] ; then
    echo "done!"
else
    echo "ERROR!"
    exit 1
fi

echo -n "    Runnning cold start..."
mpirun --allow-run-as-root -np $np $exepath/padcirc > padcirc_log.txt
exitstat=$?
echo "Finished"
echo "    PADCIRC Exit Code: $exitstat"
if [ "x$exitstat" != "x0" ] ; then
    echo "    ERROR: ADCIRC did not exit cleanly."
    exit 1
fi
echo ""


#...Run the comparison test
echo -n "    Running cold start comparison..."
for((i=0;i<$nfiles;i++))
do
    echo "" >> comparison.log
    echo "${files[$i]}" >> comparison.log
    $exepath/adcircResultsComparison -t $err -f1 ${files[$i]} -f2 control/${files[$i]} >> comparison.log 2>>comparison.log
    cserror[$i]=$?
done
echo "Finished"

#...Check the number of failed steps
fail=0
for((i=0;i<$nfiles;i++))
do
    echo -n "      "${files[$i]}": "
    if [ "x${cserror[$i]}" != "x0" ] ; then
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

if [ $fail == 1 ] ; then
    echo "|---------------------------------------------|"
    echo ""
    exit 1
fi

echo ""
cd ../02_hs

#...Grab the hotstart data
./copy_hotstart.sh

echo -n "    Prepping case..."
$exepath/adcprep --np $np --partmesh >  adcprep.log
$exepath/adcprep --np $np --prepall  >> adcprep.log
if [ $? == 0 ] ; then
    echo "done!"
else
    echo "ERROR!"
    exit 1
fi
echo -n "    Runnning hot start..."
mpirun --allow-run-as-root -np $np $exepath/padcirc > padcirc_log.txt
exitstat=$?
echo "Finished"
echo "    PADCIRC Exit Code: $exitstat"
if [ "x$exitstat" != "x0" ] ; then
    echo "    ERROR: ADCIRC did not exit cleanly."
    exit 1
fi
echo ""

#...Run the comparison test
echo -n "    Running hot start comparison..."
for((i=0;i<$nfiles;i++))
do
    echo "" >> comparison.log
    echo "${files[$i]}" >> comparison.log
    $exepath/adcircResultsComparison -t $err -f1 ${files[$i]} -f2 control/${files[$i]} >> comparison.log 2>>comparison.log
    hserror[$i]=$?
done
echo "Finished"

#...Check the number of failed steps
fail=0
for((i=0;i<$nfiles;i++))
do
    echo -n "      "${files[$i]}": "
    if [ "x${hserror[$i]}" != "x0" ] ; then
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

#!/bin/bash

case_name="adcirc_swan_apes_irene"

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

nfiles=22
files=( "fort.63" "fort.73" "maxele.63" "maxvel.63" "minpr.63" "swan_DIR.63" \
        "swan_HS.63" "swan_TM01.63" "swan_TM02.63" "swan_TMM10.63" "swan_TPS.63" \
        "fort.64" "fort.74" "maxrs.63" "maxwvel.63" "rads.64" "swan_DIR_max.63" \
        "swan_HS_max.63" "swan_TM01_max.63" "swan_TM02_max.63" "swan_TMM10_max.63" \
        "swan_TPS_max.63" )

#...Run the case
echo ""
echo "|---------------------------------------------|"
echo "    TEST CASE: $case_name"
echo ""
echo -n "    Runnning case..."
$exepath/adcswan > adcswan_log.txt
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
    if [[ ${files[$i]} == "*max*" || ${files[$i]} == "*min*" ]]; then
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

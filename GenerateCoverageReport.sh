#!/bin/bash

if [ $# != 2 ] ; then
    echo "ERROR: Must include two arguments with executable name and directory to generate coverage report for"
    exit 1
fi

#...Move into the source code object directory
cd $2

execLines=0
totalLines=0

gcovexe=$(which gcov)
if [ "x$gcovexe" == "x" ] ; then
    echo "ERROR: No gcov executable found"
    exit 1
fi

header=$(printf "%55.55s" "$1 CODE COVERAGE REPORT")
echo "|--------------------------------------------------------------------------------------|"
echo "| $header                              |"
echo "|--------------------------------------------------------------------------------------|"
echo "|              FILE              | LINES IN FILE | LINES EXECUTED | PERCENT COVERAGE   |"
echo "|--------------------------------------------------------------------------------------|"
#...Loop over output files
for OBJECT in *.o
do
    temp=$(gcov $OBJECT 2>/dev/null)
    if [ "x$temp" != "x" ] ; then
        file=$(basename $(echo $temp | cut -d\' -f2 | cut -d\' -f1))
        percent=$(echo $temp | cut -d: -f2 | cut -d% -f1)
        lines=$(echo $temp | cut -d% -f2 | cut -d" " -f3)
       
        execd=$(echo "$lines * $percent / 100" | bc)
        execLines=$(echo "$execLines + $execd" | bc)
        totalLines=$(echo "$totalLines + $lines" | bc)
        
        ps=$(printf "%18.18s" $percent)
        le=$(printf "%14.14s" $execd)
        ln=$(printf "%13.13s" $lines)
        fl=$(printf "%30.30s" $file)
        echo "| $fl | $ln | $le | $ps |"
    fi
done
echo "|--------------------------------------------------------------------------------------|"
el=$(printf "%8.8s" $execLines)
tl=$(printf "%8.8s" $totalLines)
tc=$(echo "scale=2;$el/$tl" | bc)
tp=$(printf "%0.2f" $tc)
tp=$(printf "%8.8s" $tp)
echo "  Total Lines Executed: $el"
echo "   Total Lines in Code: $tl"
echo "Total percent coverage: $tp%"

exit 0

#!/bin/bash

if [ $# != 1 ] ; then
    echo "ERROR: Specify the build directory to generate the coverage report"
    exit 1
fi

lcovexe=$(which lcov)
if [ "x$lcovexe" == "x" ] ; then
    echo "ERROR: No lcov executable found"
    exit 1
fi

genhtmlexe=$(which genhtml)
if [ "x$genhtmlexe" == "x" ] ; then
    echo "ERROR: No generate html executable found"
    exit 1
fi

basedir=$1/CMakeFiles
dirs=("adccmp.dir adcirc.dir" "adcircResultsComparison.dir" "adcprep.dir" "adcswan.dir" \
      "aswip.dir build13.dir" "buildstwave23.dir" "hot2asc.dir" "hstime.dir" "inflate.dir" \
      "metis.dir" "mkdir.dir" "owi22.dir" "p15.dir" "padcirc.dir" "padcswan.dir" \ 
      "templib_adcirc1.dir" "templib_adcswan1.dir" "templib_adcswan2.dir" \
      "templib_adcswan3.dir" "templib_padcirc1.dir" "templib_padcirc2.dir" "templib_padcirc3.dir" \
      "templib_padcswan1.dir" "templib_padcswan2.dir" "templib_padcswan3.dir" "templib_padcswan4.dir" \
      "templib_padcswan5.dir" "templib_swan1parallel.dir" "templib_swan2parallel.dir" 
      "templib_swan1serial.dir" "templib_swan2serial.dir")

#...Generate the trace files
mkdir -p adcirc.cov
cd adcirc.cov 

echo "Processing coverage files..."
testString=""
for DIR in ${dirs[@]}
do
    $lcovexe -t "adcircTestSuite" -o $DIR.info -c -d $basedir/$DIR > stat.txt 2>stat.txt
    n=$(grep "skipping" stat.txt | wc -l)
    if [ "x$n" == "x0" ] ; then
        testString="$testString -a $DIR.info" 
    fi
done
    
#...Merge data in lcov 
echo "Merging coverage files..."
$lcovexe $testString -o adcirc_full.info >/dev/null 2>/dev/null 

#...Generate the HTML
echo "Generating webpage..."
$genhtmlexe --legend --num-spaces 4 -f -o adcirc adcirc_full.info >/dev/null 2>/dev/null

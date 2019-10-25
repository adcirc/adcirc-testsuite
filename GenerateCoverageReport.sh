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

versionString=$(git --git-dir $1/../.git --work-tree $1/../ describe --always --tags)

basedir=$1/CMakeFiles

i=0
for F in $(find $1 -name "*.gcda") 
do 
    tmp=($(echo $F | sed 's/CMakeFiles/\n/g'))
    tmp1=${tmp[1]}
    tmp1=$(echo $tmp1 | cut -d/ -f2)
    if [[ $tmp1 == *".dir"* ]] ; then
        tmpdirs[$i]=$tmp1
        i=$(expr $i + 1)
    fi
done
dirs=($(echo "${tmpdirs[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

#...Generate the trace files
mkdir -p adcirc.cov
cd adcirc.cov 

echo "Processing coverage files..."
testString=""
for DIR in ${dirs[@]}
do
    $lcovexe -t "adcirc_$versionString" -o $DIR.info -c -d $basedir/$DIR > stat.txt 2>stat.txt
    n=$(grep "skipping" stat.txt | wc -l)
    if [ "x$n" == "x0" ] ; then
        testString="$testString -a $DIR.info" 
    fi
done
    
#...Merge data in lcov 
echo "Merging coverage files..."
$lcovexe $testString -o adcirc_$versionString.info >/dev/null 2>/dev/null 

#...Generate the HTML
echo "Generating webpage..."
$genhtmlexe --legend --num-spaces 4 -f -o adcirc adcirc_$versionString.info >/dev/null 2>/dev/null

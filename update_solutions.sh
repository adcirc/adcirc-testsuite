#!/bin/bash

types=("adcirc" ) # "adcirc-swan")

for T in ${types[@]}
do
    for SIMDIR in $(ls $T)
    do
        if [ -d adcirc/$SIMDIR/01_cs ] ; then
            cold_files=$(ls adcirc/$SIMDIR/01_cs/control)
    	    hot_files=$(ls adcirc/$SIMDIR/02_hs/control)
    	    cd adcirc/$SIMDIR/01_cs
    	    mv $cold_files control/.
    	    cd ..
    	    cd 02_hs
    	    mv $hot_files control/.
    	    cd ../../..
        else
            files=$(ls adcirc/$SIMDIR/control)
    	    cd adcirc/$SIMDIR
    	    mv $files control/.
    	    cd ../..
        fi
    done
done

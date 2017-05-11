#!/bin/bash

DEST_MEASUREMENTS_PATH="/Capturas/test_bw_switches3/"

mkdir $DEST_MEASUREMENTS_PATH
for i in 2 4 8 16 32 64 ; do
	mn -c;
	echo $i;
	mkdir "$DEST_MEASUREMENTS_PATH"$i"sw/"
	python test_BW2_tree_topo.py -C 12 -H 1024 -t 30 -S $i -o "$DEST_MEASUREMENTS_PATH"$i"sw/";
done

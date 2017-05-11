#!/bin/bash

DEST_MEASUREMENTS_PATH="/Capturas/test_rules1000_ping/"

mkdir $DEST_MEASUREMENTS_PATH

for j in 2 4 8 16 32 64; do

	echo $j
	mkdir $DEST_MEASUREMENTS_PATH/$j
		mn -c;
		sleep 5
		python test_RTT_subnets_topo.py -C 12 -H 1024 -t 30 -S $j -o "$DEST_MEASUREMENTS_PATH"$j"/";
		mn -c;
		sleep 5
done

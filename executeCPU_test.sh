#!/bin/bash

output_file="/Capturas/test_cpu_ping_tiempo_cte/"
DEST_MEASUREMENTS_PATH="/Capturas/ping"


mkdir $output_file/
for j in 2 4 8 16 32 64 128 256 512 1024; do
	
	mkdir $output_file/$j
	for i in 2 4 8 16 32 64 128 256 512 1024; do

		echo "Hosts: "$i" Switches: "$j
		mn -c;
		echo $i;
		./cpu.sh > $output_file/$j/$i"cpu".txt &
		./mem.sh > $output_file/$j/$i"mem".txt &
		./monitorService.sh ping > $output_file/$j/$i"activity.txt" &
		sleep 5
		python test_CPU_tree_topo.py -C 24 -H $i -t 30 -S $j -o $DEST_MEASUREMENTS_PATH;

		echo "Cleaning ...."
		mn -c;
		service openvswitch-switch stop
		rm -rf /var/log/openvswitch/*
		rm -rf /etc/openvswitch/conf.db
		service openvswitch-switch start
		mn -c
		sleep 5
		killall -9 cpu.sh
		killall -9 mem.sh
		killall -9 monitorService.sh
		echo "3" > /proc/sys/vm/drop_caches 

	done
done

#!/bin/bash
rm -rf /var/log/openvswitch/*
for l in {1..99}; do

output_file="/Capturas/test_cpu_ping_tiempo_cte_DB_isolcpus_2core/n"$l"/"
DEST_MEASUREMENTS_PATH="/Capturas/ping"

mkdir $output_file/
for j in 2 4 8 16 32 64 128 200 256 400 512 700 1024; do
	
	mkdir $output_file/$j
	for i in 2 4 8 16 32 64 128 256 512 1024; do

		echo "Hosts: "$i" Switches: "$j
		mn -c;

		service openvswitch-switch stop
		rm /etc/openvswitch/*
		ovs-appctl -t ovs-vswitchd exit
		ovs-appctl -t ovsdb-server exit
		ovs-dpctl del-dp system@ovs-system
		rmmod openvswitch
		service openvswitch-switch start


		echo $i;
		taskset -c 5 ./cpu.sh > $output_file/$j/$i"cpu".txt &
		taskset -c 5 ./mem.sh > $output_file/$j/$i"mem".txt &
		taskset -c 5 ./monitorService.sh ping > $output_file/$j/$i"activity.txt" &
		sleep 5
		taskset -c 4 python test_CPU_tree_topo.py -C 12 -H $i -t 30 -S $j  -o $DEST_MEASUREMENTS_PATH;

		echo "Cleaning ...."
		mn -c;

		sleep 5
		killall -9 cpu.sh
		killall -9 mem.sh
		killall -9 monitorService.sh
		echo "3" > /proc/sys/vm/drop_caches 

	done
done

done

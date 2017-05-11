#!/bin/bash

while [ 1 -eq 1 ] ; do
    echo $(date +%s)","$(free -m | grep "Mem" | awk '{print ($4+$7)/$2*100}')

    sleep 1
done



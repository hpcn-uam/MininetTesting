#!/bin/bash

while [ 1 -eq 1 ]; do

echo $(date +%s)","$(ps aux | grep $1 | grep -v "grep\|monitorService" | wc -l)","$(ps aux | grep 'mininet:h' | grep -v grep | wc -l)
sleep 1
done

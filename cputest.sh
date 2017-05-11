#!/bin/bash
#base on the proposed solution by user Fidel at
#http://stackoverflow.com/questions/23367857/accurate-calculation-of-cpu-usage-given-in-percentage-in-linux/23376195

sleepDurationSeconds=$1

previousDate=$(date +%s%N | cut -b1-13)
previousStats=$(cat /proc/stat)

sleep $sleepDurationSeconds

line=$(date +%s)" "


currentDate=$(date +%s%N | cut -b1-13)
currentStats=$(cat /proc/stat)    

cpus=$(echo "$currentStats" | grep -P 'cpu' | awk -F " " '{print $1}')

for cpu in $cpus
do
    currentLine=$(echo "$currentStats" | grep "$cpu ")
    user=$(echo "$currentLine" | awk -F " " '{print $2}')
    nice=$(echo "$currentLine" | awk -F " " '{print $3}')
    system=$(echo "$currentLine" | awk -F " " '{print $4}')
    idle=$(echo "$currentLine" | awk -F " " '{print $5}')
    iowait=$(echo "$currentLine" | awk -F " " '{print $6}')
    irq=$(echo "$currentLine" | awk -F " " '{print $7}')
    softirq=$(echo "$currentLine" | awk -F " " '{print $8}')
    steal=$(echo "$currentLine" | awk -F " " '{print $9}')
    guest=$(echo "$currentLine" | awk -F " " '{print $10}')
    guest_nice=$(echo "$currentLine" | awk -F " " '{print $11}')

    previousLine=$(echo "$previousStats" | grep "$cpu ")
    prevuser=$(echo "$previousLine" | awk -F " " '{print $2}')
    prevnice=$(echo "$previousLine" | awk -F " " '{print $3}')
    prevsystem=$(echo "$previousLine" | awk -F " " '{print $4}')
    previdle=$(echo "$previousLine" | awk -F " " '{print $5}')
    previowait=$(echo "$previousLine" | awk -F " " '{print $6}')
    previrq=$(echo "$previousLine" | awk -F " " '{print $7}')
    prevsoftirq=$(echo "$previousLine" | awk -F " " '{print $8}')
    prevsteal=$(echo "$previousLine" | awk -F " " '{print $9}')
    prevguest=$(echo "$previousLine" | awk -F " " '{print $10}')
    prevguest_nice=$(echo "$previousLine" | awk -F " " '{print $11}')    

    PrevIdle=$((previdle + previowait))
    Idle=$((idle + iowait))

    PrevNonIdle=$((prevuser + prevnice + prevsystem + previrq + prevsoftirq + prevsteal))
    NonIdle=$((user + nice + system + irq + softirq + steal))

    PrevTotal=$((PrevIdle + PrevNonIdle))
    Total=$((Idle + NonIdle))

    totald=$((Total - PrevTotal))
    idled=$((Idle - PrevIdle))

    CPU_Percentage=$(awk "BEGIN {print ($totald - $idled)/$totald*100}")

    if [[ "$cpu" == "cpu" ]]; then
        line=$line" all "$CPU_Percentage
    else
        line=$line" "$cpu" "$CPU_Percentage
    fi
done
    echo $line

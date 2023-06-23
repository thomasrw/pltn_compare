#!/bin/sh

task_id=$1
loop_number=$2
now=$(date)
mycpu=$(awk '{print $39}' /proc/self/stat)
echo "Task $task_id loop number $loop_number begun $now on core $mycpu"
j=1
end=$((SECONDS+60))
while [ $SECONDS -lt $end ]; do
j=$((j + 1))
done
now=$(date)
echo "Task $task_id loop number $loop_number completed $now on core $mycpu"



#echo "Task $SLURM_TASK_PID: Message $i executed on CPU core:" &
#awk '{print $39}' /proc/$SLURM_TASK_PID/stat


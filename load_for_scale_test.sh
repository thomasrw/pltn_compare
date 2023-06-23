#!/bin/sh

task_id=$1
loop_number=$2
now=$(date)
mycpu=$(awk '{print $39}' /proc/$task_id/stat)
echo "Task $task_id loop number $loop_number begun $now on core $mycpu"
sleep 60
now=$(date)
echo "Task $task_id loop number $loop_number completed $now on core $mycpu"



#echo "Task $SLURM_TASK_PID: Message $i executed on CPU core:" &
#awk '{print $39}' /proc/$SLURM_TASK_PID/stat


#!/bin/sh

task_id=$1
now=$(date)
mycpu=$(awk '{print $39}' /proc/$task_id/stat)
echo "Task $task_id begun $now on core $mycpu"
sleep 60
echo $(date)


#echo "Task $SLURM_TASK_PID: Message $i executed on CPU core:" &
#awk '{print $39}' /proc/$SLURM_TASK_PID/stat


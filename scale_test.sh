#!/bin/sh

#SBATCH --array=1-2
#SBATCH --partition=defq-64core #temp during defq maintenance
##SBATCH -N 1     #nodes requested
#SBATCH -n 10     #tasks requested changed to number of cores needed per Nathan Elger guidance
##SBATCH -c 10    #cpus per task commented out per Nathan Elger guidance	
##SBATCH -x /work/public/exclude_defq #avoids use of partner nodes subj to suspension #temp remove during defq maintenance check before next submission
##SBATCH --output=/dev/null  #suppress standard output
#SBATCH --output=/work/thoma525/slurm_errors-%A.out
#SBATCH --open-mode=append
#SBATCH --error=/work/thoma525/slurm_errors-%j.out   #suppress standard error

##todo run demand_formatter.py on CAV [arg1] _ [arg2] to ensure catchup properly defined
##todo CAV [array task] for inputs 100-199 for sizes x
#todo Gather metrics for CAV [array task] for inputs 100-199
#todo remove all logfiles generated leaving only metrics.csv files for CAV [array task]_size

module load sumo
module load python3/anaconda/2019.03

export SUMO_HOME=/work/apps/sumo/share/sumo

#run CAV008 100-199 for pln_size 1-10, with 1 being no limit (anything < 1 not enforced)
#TEST_NUM=$((SLURM_ARRAY_TASK_ID + 99))

SIZE="8"
PERCENT=$(printf "%03d" $SLURM_ARRAY_TASK_ID)

i="0"
while [ $i -lt 10 ]
do
echo "Task $SLURM_TASK_PID: Message $i executed on CPU core $SLURM_NPROCS or $SLURM_NTASKS"
i=$((i + 1))
done
wait

echo success $SLURM_ARRAY_TASK_ID



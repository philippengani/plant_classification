#!/bin/bash

#SBATCH --workdir /home/mohanty/caffe_experiments/AWS_FRESH_RUN/experiment_configs/alexnet/color-20-80/train_from_scratch
#SBATCH --nodes 1
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 2
#SBATCH --mem 16384
#SBATCH --time 23:59:59
#SBATCH --partition gpu
#SBATCH --gres gpu:2
#SBATCH --qos gpu

#STARTING AT Sat Mar 21 02:56:54 EDT 2020
#FINISHED at Sat Mar 21 03:56:50 EDT 2020

#module add caffe
#module add cuda
echo STARTING AT `date`

caffe train -solver solver.prototxt -gpu all &> caffe.log

#sbatch test.sh
echo FINISHED at `date`

#!/bin/bash
#SBATCH --requeue
#SBATCH --account=sua183
#SBATCH --output=data/log/job_out_1.log
#SBATCH --error=data/log/job_err_1.log
#SBATCH --partition=compute
#SBATCH --job-name=1_DFTMC
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=128
#SBATCH --mem=249325M
#SBATCH --time=48:00:00

# module --force purge
# ml load cpu slurm gcc openmpi anaconda3
module purge
module load shared
module load slurm/expanse/current
module load cpu/0.15.4
module load DefaultModules
module load gcc/9.2.0
module load openmpi/3.1.6
module load openblas/0.3.10-openmp
module load netlib-scalapack/2.1.0-openblas
module load fftw/3.3.8
module load anaconda3/2020.11

export OMPI_MCA_btl=self,vader
SECONDS=0
./MC.sh VASP 5001 128 /home/yifanc/MC_simulations/01_MC_20220328/01_SQS_generation/Random_structures_108/POSCAR_1 \
./data/run_folder_1/ ./data/structures_1/ 1 500
duration=$SECONDS
echo "Total job time: $duration seconds"
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

# Load necessary modules, example:
# Basic modules
module purge
module load shared
module load slurm/expanse/current
module load cpu/0.15.4
module load DefaultModules
module load gcc/9.2.0

# VASP-specific modules
module load openmpi/3.1.6
module load openblas/0.3.10-openmp
module load netlib-scalapack/2.1.0-openblas
module load fftw/3.3.8

# Python environment
module load anaconda3/2020.11

# Set VASP executable path
export VASP_PATH=/home/yifanc/MD_intro/vasp.6.2.1/bin/vasp_gam

export OMPI_MCA_btl=self,vader
SECONDS=0

# Create necessary directories
mkdir -p ./data/run_folder_1
mkdir -p ./data/structures_1
mkdir -p ./data/log

python MC.py 5001 128 \
    ./random_structures/POSCAR_1 \
    ./data/run_folder_1/ \
    ./data/structures_1/ \
    1 \
    500

duration=$SECONDS
echo "Total job time: $duration seconds" 
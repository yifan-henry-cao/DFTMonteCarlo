#!/usr/bin/env python3

import os
import sys
import shutil
import time
from pathlib import Path
import subprocess
from .mc_utils import MCRunner

def ensure_directory(path):
    """Create directory if it doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)

def copy_vasp_inputs(source_dir, run_dir):
    """Copy VASP input files from source directory"""
    required_files = ['INCAR', 'POTCAR', 'KPOINTS']
    
    if not os.path.exists(source_dir):
        print(f"Error: Source directory {source_dir} does not exist!")
        sys.exit(1)
        
    for file in required_files:
        src_file = os.path.join(source_dir, file)
        if not os.path.exists(src_file):
            print(f"Error: Required file {file} not found in {source_dir}")
            sys.exit(1)
        shutil.copy2(src_file, run_dir)
    
    print(f"Copied VASP input files from {source_dir} to {run_dir}")

def main():
    # Parse command line arguments
    if len(sys.argv) != 9:
        print("Usage: python DFTMC.py max_iteration num_cores in_dir run_dir save_dir save_freq T source_dir")
        sys.exit(1)

    max_iteration = int(sys.argv[1])
    num_cores = sys.argv[2]
    in_dir = sys.argv[3]
    run_dir = sys.argv[4]
    save_dir = sys.argv[5]
    save_freq = int(sys.argv[6])
    temperature = sys.argv[7]
    source_dir = sys.argv[8]  # New argument for source directory

    # Check input file exists
    if not os.path.exists(in_dir):
        print(f"Error: Input structure file {in_dir} does not exist!")
        sys.exit(1)

    # Create necessary directories
    ensure_directory(run_dir)
    ensure_directory(save_dir)

    # Copy VASP input files
    copy_vasp_inputs(source_dir, run_dir)

    # Initialize MC runner
    mc = MCRunner(run_dir, save_dir, temperature)

    # Set environment variables and paths
    os.environ['OMP_NUM_THREADS'] = '1'

    # Get VASP path from environment variable
    vasp_path = os.getenv('VASP_PATH')
    if not vasp_path:
        print("Error: VASP_PATH environment variable is not set. Please set it to point to your VASP executable.")
        sys.exit(1)
    if not os.path.exists(vasp_path):
        print(f"Error: VASP executable not found at {vasp_path}")
        sys.exit(1)
    vasp_cmd = f"mpirun -np {num_cores} {vasp_path}"
    mclog_path = os.path.join(save_dir, 'MClog')

    # Check if this is a restart or fresh run
    if os.path.exists(mclog_path):
        print(f"{mclog_path} exists, reading last step info")
        istart, last_energy = mc.read_last_step(mclog_path)
        mc.prepare_step(istart, os.path.join(save_dir, f"POSCAR_{istart}"), restart=True)
        mc.restore_accepted_energy(last_energy)
    else:
        print(f"{mclog_path} does not exist. Initializing..")
        istart = 0
        mc.prepare_step(istart, in_dir, restart=True)

        # Run initial VASP calculation
        t0 = time.time()
        subprocess.run(vasp_cmd, shell=True, check=True, cwd=run_dir)
        runtime = time.time() - t0

        # Process results
        mc.finalize_step(istart, save_freq, restart=True, runtime=runtime)
        print(f"step {istart}: runtime={runtime:.1f}s accept=True (restart)")

    # Main Monte Carlo loop
    for i in range(istart + 1, max_iteration):
        # Prepare next iteration
        mc.prepare_step(i, os.path.join(run_dir, "accepted_POSCAR"), restart=False)

        # Run VASP
        t0 = time.time()
        subprocess.run(vasp_cmd, shell=True, check=True, cwd=run_dir)
        runtime = time.time() - t0

        # Process results
        accept = mc.finalize_step(i, save_freq, restart=False, runtime=runtime)
        print(f"step {i}: runtime={runtime:.1f}s accept={accept}")

if __name__ == "__main__":
    main() 
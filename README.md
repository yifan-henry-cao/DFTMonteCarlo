# DFTMonteCarlo

Monte Carlo simulation with DFT energy calculations using VASP.

## Description

This package implements a Monte Carlo algorithm for atomic structure sampling, using VASP for energy calculations. It supports:
- Atomic swaps for structure evolution
- Metropolis acceptance criterion
- Restart capability
- Configurable saving frequency

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd DFTMonteCarlo
   ```

2. Create and activate a new conda environment (recommended):
   ```bash
   conda create -n dft-mc python=3.9
   conda activate dft-mc
   ```

3. Install the package:
   ```bash
   # For basic installation
   pip install -r requirements.txt

   # For development installation (includes testing tools)
   pip install -e ".[dev]"
   ```

## Dependencies

Core dependencies:
- pymatgen (>= 2023.0.0): For structure manipulation and I/O
- numpy (>= 1.20.0): For numerical operations

Optional dependencies:
- scipy (>= 1.7.0): Scientific computing tools
- matplotlib (>= 3.4.0): For plotting (if needed)

Development dependencies:
- pytest (>= 6.0.0): For running tests
- black (>= 22.0.0): For code formatting
- pylint (>= 2.8.0): For code linting

## Usage

1. Prepare your input structure in VASP POSCAR format

2. Configure your VASP path in the job script:
   ```bash
   export VASP_PATH=/path/to/vasp/binary
   ```

3. Run the Monte Carlo simulation:
   ```bash
   python MC.py max_iteration num_cores in_dir run_dir save_dir save_freq T
   ```

Arguments:
- max_iteration: Maximum number of Monte Carlo steps
- num_cores: Number of CPU cores for VASP calculation
- in_dir: Path to input structure file
- run_dir: Directory for running calculations
- save_dir: Directory for saving results
- save_freq: Frequency of saving intermediate results
- T: Temperature for Metropolis criterion (K)

See the example directory for a complete job script example.

## Directory Structure

- bin/: Executable scripts
- src/: Source code
- example/: Example job scripts and input files
- tests/: Test files (if any)

## Notes

- Requires VASP to be installed and accessible
- Designed for HPC environments with SLURM job scheduler
- Supports restart from previous calculations
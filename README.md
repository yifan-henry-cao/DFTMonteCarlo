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
   git clone https://github.com/yifan-henry-cao/DFTMonteCarlo.git
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
   pip install -e .

   # For development installation (includes testing tools)
   pip install -e ".[dev]"
   ```

## Dependencies

Core dependencies:
- pymatgen (>= 2022.2.10): For structure manipulation and I/O
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

3. Run the Monte Carlo simulation. You can use any of these methods:
   ```bash
   # As a Python module (recommended)
   python -m dftmc.DFTMC max_iteration num_cores in_dir run_dir save_dir save_freq T source_dir

   # Using the console script
   dftmc max_iteration num_cores in_dir run_dir save_dir save_freq T source_dir
   ```

Arguments:
- max_iteration: Maximum number of Monte Carlo steps
- num_cores: Number of CPU cores for VASP calculation
- in_dir: Path to input structure file
- run_dir: Directory for running calculations
- save_dir: Directory for saving results
- save_freq: Frequency of saving intermediate results
- T: Temperature for Metropolis criterion (K)
- source_dir: Directory containing VASP input files (INCAR, POTCAR, KPOINTS)

See the example directory for a complete job script example.

## Directory Structure

```
DFTMonteCarlo/
├── dftmc/                     # Main package directory
│   ├── __init__.py           # Package initialization
│   ├── DFTMC.py              # Main script
│   └── mc_utils.py           # Core functionality
├── example/
│   ├── example.sh            # Example job script
│   └── random_structures/    # Example input structures
├── setup.py                  # Installation configuration
├── requirements.txt          # Package dependencies
└── README.md                 # This file
```

## Notes

- Requires VASP to be installed and accessible
- Designed for HPC environments with SLURM job scheduler
- Supports restart from previous calculations
- Can be run from any directory after installation

## For Developers

You can also use the package programmatically:
```python
from dftmc import MCRunner

# Initialize MC runner
mc = MCRunner(run_dir="./run", save_dir="./save", temperature=500)

# Use mc_runner methods directly
mc.prepare_step(step=0, input_file="POSCAR", restart=True)
```
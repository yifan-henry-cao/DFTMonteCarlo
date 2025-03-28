# from time import perf_counter
# t0 = perf_counter()
import numpy as np
from numpy import *
import sys
from pymatgen.core import Structure
sys.path.append("/home/yifanc/MC_simulations/util")
from Pymat_IO import *

# Read in the current time step and suggest a new flip
# Input arguments: flag=(LAMMPS or VASP) cur_step in_dir run_dir restart_flag
# flag: determines energy source and how to read them
# cur_step: current timestep of Monte Carlo algorithm
# in_dir: location of the input structure file
# run_dir: the directory where datafiles are located
# restart_flag: whether this run is directly after restart or not (1 for restart, 0 for continue)

if len(sys.argv)==6:
    flag = sys.argv[1]
    cur_step = int(sys.argv[2])
    in_dir = sys.argv[3]
    run_dir = sys.argv[4]
    restart_flag = int(sys.argv[5])
else:
    print("Incorrect amount of inputs given!")
    exit()

if flag=="LAMMPS":
    if restart_flag:
        structure = Structure.from_file(in_dir, sort=True)
        Write_to_data(structure, "{}structure.data".format(run_dir))
        Write_to_poscar(structure, "{}POSCAR".format(run_dir))
        Write_to_poscar(structure, "{}accepted_POSCAR".format(run_dir))
    else:
        structure = Structure.from_file(in_dir, sort=True)
        natoms = len(structure)
        i1, i2 = np.random.choice(natoms, 2)
        while structure.species[i1]==structure.species[i2]:
                i1, i2 = np.random.choice(natoms, 2)
        t1 = structure.species[i1]
        structure[int(i1)] = structure.species[i2]
        structure[int(i2)] = t1
        Write_to_data(structure, "{}structure.data".format(run_dir))
        Write_to_poscar(structure, "{}POSCAR".format(run_dir))
elif flag=="VASP":
    if restart_flag:
        structure = Structure.from_file(in_dir, sort=True)
        Write_to_poscar(structure, "{}POSCAR".format(run_dir))
        Write_to_poscar(structure, "{}accepted_POSCAR".format(run_dir))
    else:
        structure = Structure.from_file(in_dir, sort=True)
        natoms = len(structure)
        i1, i2 = np.random.choice(natoms, 2)
        while structure.species[i1]==structure.species[i2]:
                i1, i2 = np.random.choice(natoms, 2)
        t1 = structure.species[i1]
        structure[int(i1)] = structure.species[i2]
        structure[int(i2)] = t1
        Write_to_poscar(structure.get_sorted_structure(), "{}POSCAR".format(run_dir))
else:
    print("Unrecognized Flag passed, please indicate energy source!")
    exit()

# print("MC_prep time elapsed: {} sec".format(perf_counter()-t0))
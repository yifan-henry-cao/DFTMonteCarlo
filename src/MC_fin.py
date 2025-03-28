# from time import perf_counter
# t0 = perf_counter()
import numpy as np
from numpy import *
import sys
from pymatgen.core import Structure
sys.path.append("/home/yifanc/DFT_calculations/util")
sys.path.append("/home/yifanc/MC_simulations/util")
from Pymat_IO import *
from readenergy import readenergy


# Read in the current time step and suggest a new flip
# Input arguments: flag=(LAMMPS or VASP) cur_step run_dir save_dir save_freq T restart_flag
# flag: determines energy source and how to read them
# cur_step: current timestep of Monte Carlo algorithm
# run_dir: the directory where datafiles are located
# save_dir: the directory to save intermediate structures and MClog
# save_freq: the frequency of saving data
# T: annealing temperature in the Metropolis-Hastings algorithm
# restart_flag: whether this run is directly after restart or not (1 for restart, 0 for continue)


def get_energy(energy_source, file_dir):
    # Read in system energy after proposed flip
    if energy_source=="VASP":
        energy = readenergy("{}OSZICAR".format(file_dir))
    elif energy_source=="LAMMPS":
        energy = float(np.loadtxt("{}thermo.dat".format(file_dir), unpack=True, usecols=3))
    else:
        print("Unrecognized energy source!")
        sys.exit()
    return energy

if len(sys.argv)==8:
    flag = sys.argv[1]
    cur_step = int(sys.argv[2])
    run_dir = sys.argv[3]
    save_dir = sys.argv[4]
    save_freq = int(sys.argv[5])
    T = float(sys.argv[6])
    restart_flag = int(sys.argv[7])
else:
    print("Incorrect amount of inputs given!")
    exit()

if restart_flag:
    energy_flip = get_energy(flag, run_dir)
    with open("{}accepted_energy".format(run_dir), 'w') as f:
        f.write(str(energy_flip))
    with open("{}MClog".format(save_dir), "a") as f:
        f.write("{} {} {}\n".format(cur_step, energy_flip, 1))
else:
    kb = 8.617333262E-5
    with open("{}accepted_energy".format(run_dir), 'r') as f:
        current_energy = float(f.readline())
    energy_flip = get_energy(flag, run_dir)
    r = np.random.random()

    # Decide whether to update energy and structure
    if r < min(1, np.exp(-(energy_flip - current_energy) /  (kb * T))):
        accept = 1
        current_energy = energy_flip
        structure = Structure.from_file("{}POSCAR".format(run_dir), sort=True)
        Write_to_poscar(structure, "{}accepted_POSCAR".format(run_dir))
        with open("{}accepted_energy".format(run_dir), 'w') as f:
            f.write(str(energy_flip))
    else:
        accept = 0
    
    # Saving outputs to save_dir and MClog
    if cur_step % save_freq == 0:
        structure = Structure.from_file("{}accepted_POSCAR".format(run_dir), sort=True)
        Write_to_poscar(structure, "{}POSCAR_{}".format(save_dir, cur_step))
        with open("{}MClog".format(save_dir), "a") as f:
            f.write("{} {} {}\n".format(cur_step, current_energy, accept))

# print("MC_fin time elapsed: {} sec".format(perf_counter()-t0))
import os
import numpy as np
from pymatgen.core import Structure
from pymatgen.io.vasp.inputs import Poscar
from pymatgen.io.lammps.data import LammpsData

class MCRunner:
    def __init__(self, run_dir, save_dir, temperature):
        """
        Initialize MC simulation parameters
        
        Args:
            run_dir: Directory for running calculations
            save_dir: Directory for saving results
            temperature: Temperature for MC simulation in Kelvin
        """
        self.run_dir = run_dir
        self.save_dir = save_dir
        self.temperature = float(temperature)
        self.kb = 8.617333262E-5  # Boltzmann constant in eV/K

    def write_structure(self, structure, filename, fmt='poscar', suppress_output=True):
        """Write structure to file in specified format"""
        if fmt.lower() == 'poscar':
            structure_out = Poscar(structure)
            structure_out.write_file(filename)
        elif fmt.lower() == 'data':
            structure_out = LammpsData.from_structure(structure)
            structure_out.write_file(filename)
        
        if not suppress_output:
            print(f"File successfully written to: {filename}")

    def read_vasp_energy(self, filename):
        """Read the last energy from VASP OSZICAR file"""
        with open(filename, 'rb') as f:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
            last_line = f.readline().decode()
            E_string = last_line.split()[4]
        return float(E_string)

    def prepare_step(self, step, input_file, restart=False):
        """
        Prepare structure for the next MC step
        
        Args:
            step: Current MC step number
            input_file: Input structure file path
            restart: Whether this is a restart step
        """
        structure = Structure.from_file(input_file, sort=True)
        
        if not restart:
            # Perform atom swap
            natoms = len(structure)
            i1, i2 = np.random.choice(natoms, 2)
            while structure.species[i1] == structure.species[i2]:
                i1, i2 = np.random.choice(natoms, 2)
            
            # Swap atoms
            t1 = structure.species[i1]
            structure[int(i1)] = structure.species[i2]
            structure[int(i2)] = t1
            structure = structure.get_sorted_structure()
        
        # Write new structure
        self.write_structure(structure, f"{self.run_dir}/POSCAR")
        if restart:
            self.write_structure(structure, f"{self.run_dir}/accepted_POSCAR")

    def finalize_step(self, step, save_freq, restart=False):
        """
        Process results after energy calculation
        
        Args:
            step: Current MC step number
            save_freq: Frequency to save intermediate results
            restart: Whether this is a restart step
        
        Returns:
            bool: Whether the step was accepted
        """
        energy_flip = self.read_vasp_energy(f"{self.run_dir}/OSZICAR")
        
        if restart:
            # For restart steps, always accept
            with open(f"{self.run_dir}/accepted_energy", 'w') as f:
                f.write(str(energy_flip))
            with open(f"{self.save_dir}/MClog", "a") as f:
                f.write(f"{step} {energy_flip} 1\n")
            return True
        
        # Read current accepted energy
        with open(f"{self.run_dir}/accepted_energy", 'r') as f:
            current_energy = float(f.readline())
        
        # Metropolis acceptance criterion
        accept = False
        if np.random.random() < min(1, np.exp(-(energy_flip - current_energy) / (self.kb * self.temperature))):
            accept = True
            current_energy = energy_flip
            structure = Structure.from_file(f"{self.run_dir}/POSCAR", sort=True)
            self.write_structure(structure, f"{self.run_dir}/accepted_POSCAR")
            with open(f"{self.run_dir}/accepted_energy", 'w') as f:
                f.write(str(energy_flip))
        
        # Save intermediate results if needed
        if step % save_freq == 0:
            structure = Structure.from_file(f"{self.run_dir}/accepted_POSCAR", sort=True)
            self.write_structure(structure, f"{self.save_dir}/POSCAR_{step}")
            with open(f"{self.save_dir}/MClog", "a") as f:
                f.write(f"{step} {current_energy} {int(accept)}\n")
        
        return accept

    @staticmethod
    def read_last_step(mclog_path):
        """Read the last step number from MClog file"""
        with open(mclog_path, 'r') as f:
            last_line = f.readlines()[-1]
            return int(last_line.split()[0]) 
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
        self._last_prepared_structure = None  # structure just written to run_dir/POSCAR
        self._accepted_structure = None  # structure currently in run_dir/accepted_POSCAR

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
            if len(set(structure.species)) < 2:
                raise ValueError("Structure has fewer than 2 distinct species; no atom swap is possible")
            i1, i2 = np.random.choice(natoms, 2, replace=False)
            while structure.species[i1] == structure.species[i2]:
                i1, i2 = np.random.choice(natoms, 2, replace=False)

            # Swap atoms
            t1 = structure.species[i1]
            structure[int(i1)] = structure.species[i2]
            structure[int(i2)] = t1
            structure = structure.get_sorted_structure()

        # Write new structure
        self._last_prepared_structure = structure
        self.write_structure(structure, os.path.join(self.run_dir, "POSCAR"))
        if restart:
            self.write_structure(structure, os.path.join(self.run_dir, "accepted_POSCAR"))
            self._accepted_structure = structure

    def finalize_step(self, step, save_freq, restart=False, runtime=None):
        """
        Process results after energy calculation

        Args:
            step: Current MC step number
            save_freq: Frequency to save intermediate results
            restart: Whether this is a restart step
            runtime: Wall-clock time (seconds) the VASP call for this step took

        Returns:
            bool: Whether the step was accepted
        """
        energy_flip = self.read_vasp_energy(os.path.join(self.run_dir, "OSZICAR"))
        runtime_str = f"{runtime:.2f}" if runtime is not None else "NA"

        if restart:
            # For restart steps, always accept
            with open(os.path.join(self.run_dir, "accepted_energy"), 'w') as f:
                f.write(str(energy_flip))
            # Save a snapshot too, so a later resume from this MClog line can
            # always reload save_dir/POSCAR_{step} (mirrors the non-restart path below).
            # self._accepted_structure was just set by prepare_step, no need to re-read from disk.
            self.write_structure(self._accepted_structure, os.path.join(self.save_dir, f"POSCAR_{step}"))
            with open(os.path.join(self.save_dir, "MClog"), "a") as f:
                f.write(f"{step} {energy_flip} 1 {runtime_str}\n")
            return True

        # Read current accepted energy
        with open(os.path.join(self.run_dir, "accepted_energy"), 'r') as f:
            current_energy = float(f.readline())

        # Metropolis acceptance criterion. Clamp the exponent at 0 to avoid an
        # overflow warning from np.exp on large positive deltas (result is
        # discarded by min(1, ...) anyway).
        delta = -(energy_flip - current_energy) / (self.kb * self.temperature)
        probability = 1.0 if delta >= 0 else np.exp(delta)

        accept = False
        if np.random.random() < probability:
            accept = True
            current_energy = energy_flip
            # self._last_prepared_structure is the exact structure just written
            # to run_dir/POSCAR by prepare_step, no need to re-read from disk.
            structure = self._last_prepared_structure
            self.write_structure(structure, os.path.join(self.run_dir, "accepted_POSCAR"))
            self._accepted_structure = structure
            with open(os.path.join(self.run_dir, "accepted_energy"), 'w') as f:
                f.write(str(energy_flip))

        # Save intermediate results if needed
        if step % save_freq == 0:
            self.write_structure(self._accepted_structure, os.path.join(self.save_dir, f"POSCAR_{step}"))
            with open(os.path.join(self.save_dir, "MClog"), "a") as f:
                f.write(f"{step} {current_energy} {int(accept)} {runtime_str}\n")

        return accept

    def restore_accepted_energy(self, energy):
        """Write a previously accepted energy value into run_dir (used when resuming)"""
        with open(os.path.join(self.run_dir, "accepted_energy"), 'w') as f:
            f.write(str(energy))

    @staticmethod
    def read_last_step(mclog_path):
        """Read the last step number and its accepted energy from MClog file"""
        with open(mclog_path, 'r') as f:
            last_line = f.readlines()[-1]
        parts = last_line.split()
        return int(parts[0]), float(parts[1]) 
#from pymatgen.core import Structure
from pymatgen.io.vasp.inputs import Poscar
from pymatgen.io.lammps.data import LammpsData

def Write_to_poscar(structure, fout, suppressout=True):
    structure_poscar = Poscar(structure)
    structure_poscar.write_file(fout)
    if not suppressout:
        print("File successfully write to: " + fout)
    return 0

def Write_to_data(structure, fout, suppressout=True):
    structure_lammps = LammpsData.from_structure(structure)
    structure_lammps.write_file(fout)
    if not suppressout:
        print("File successfully write to: " + fout)
    return 0

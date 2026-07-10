import os
import re
import numpy as np
from pymatgen.core import Structure
from pymatgen.io.vasp.inputs import Poscar
from pymatgen.io.lammps.data import LammpsData

# Matches the trailing per-atom moment annotation this project already uses
# on some POSCARs, e.g. "0.75 0.75 0.75 Fe,spin=2.5" or
# "...Fe,spin=np.float64(2.5)" (see e.g.
# 01_Heusler_starup/magnetic_orderings/POSCAR_00_FM_fm).
_SPIN_RE = re.compile(r"spin=(?:np\.float64\()?([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)\)?")


def format_magmom(moments):
    """Compress a per-atom MAGMOM list into VASP's count*value shorthand."""
    out, prev, count = [], None, 0
    for m in [round(float(x), 6) for x in moments]:
        if m == prev:
            count += 1
        else:
            if prev is not None:
                out.append(f"{count}*{prev:g}" if count > 1 else f"{prev:g}")
            prev, count = m, 1
    if prev is not None:
        out.append(f"{count}*{prev:g}" if count > 1 else f"{prev:g}")
    return " ".join(out)


def read_poscar_with_spin(path):
    """
    Read a POSCAR, detecting an optional trailing ",spin=<value>" annotation
    on each coordinate line (this project's existing convention for carrying
    per-atom initial moments in a POSCAR, e.g. magnetic_orderings/POSCAR_00_FM_fm).

    Returns (structure, moments): `moments` is a list of floats (file order)
    if any "spin=" annotation was found, else None. When present, `moments`
    is also attached to the returned Structure as the "magmom" site
    property, which pymatgen correctly carries along per-site through
    species reassignment and get_sorted_structure().
    """
    structure = Structure.from_file(path, sort=False)
    matches = _SPIN_RE.findall(open(path).read())
    if not matches:
        return structure, None
    if len(matches) != len(structure):
        raise ValueError(
            f"{path}: found {len(matches)} spin= annotations but structure has {len(structure)} atoms")
    moments = [float(m) for m in matches]
    structure.add_site_property("magmom", moments)
    return structure, moments


def write_poscar_with_spin(structure, path, comment=None):
    """
    Write a Structure to POSCAR format, appending ",spin=<value>" to each
    coordinate line from the structure's "magmom" site property. Geometry/
    header lines come from pymatgen's own Poscar writer; only the per-atom
    trailing annotation is added on top, so this round-trips cleanly with
    read_poscar_with_spin() across MC steps and restarts.
    """
    moments = structure.site_properties["magmom"]
    natoms = len(structure)
    poscar = Poscar(structure, comment=comment) if comment else Poscar(structure)
    lines = poscar.get_str().splitlines()
    header_lines, coord_lines = lines[:-natoms], lines[-natoms:]
    new_coord_lines = []
    for site, line, m in zip(structure, coord_lines, moments):
        # pymatgen's own Poscar writer already appends a trailing species
        # symbol comment to each coordinate line — discard it and write our
        # own single ",spin=" annotation instead of stacking on top of it.
        x, y, z = line.split()[:3]
        new_coord_lines.append(f"{x} {y} {z} {site.specie},spin={m:g}")
    with open(path, "w") as f:
        f.write("\n".join(header_lines + new_coord_lines) + "\n")


def update_incar_magmom(incar_path, magmom_str):
    """Patch (or add) the MAGMOM line of an existing INCAR file in place."""
    with open(incar_path) as f:
        lines = f.readlines()
    pattern = re.compile(r"^\s*MAGMOM\s*=", re.IGNORECASE)
    new_line = f"MAGMOM = {magmom_str}\n"
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = new_line
            break
    else:
        lines.append(new_line)
    with open(incar_path, "w") as f:
        f.writelines(lines)


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

    def _write_structure_maybe_spin(self, structure, path):
        """Write a structure, using the spin-annotated POSCAR format if this
        structure carries a "magmom" site property, else the plain writer."""
        if "magmom" in structure.site_properties:
            write_poscar_with_spin(structure, path)
        else:
            self.write_structure(structure, path)

    def prepare_step(self, step, input_file, restart=False):
        """
        Prepare structure for the next MC step

        Args:
            step: Current MC step number
            input_file: Input structure file path
            restart: Whether this is a restart step
        """
        structure, moments = read_poscar_with_spin(input_file)
        if moments is None:
            # No per-atom moments tracked: fall back to the original
            # behavior (pymatgen's own sort, no INCAR involvement here).
            structure = Structure.from_file(input_file, sort=True)

        if not restart:
            # Perform atom swap
            natoms = len(structure)
            if len(set(structure.species)) < 2:
                raise ValueError("Structure has fewer than 2 distinct species; no atom swap is possible")
            i1, i2 = np.random.choice(natoms, 2, replace=False)
            while structure.species[i1] == structure.species[i2]:
                i1, i2 = np.random.choice(natoms, 2, replace=False)

            # Swap atoms — species and (if tracked) their moment move together,
            # so a swap relocates the whole atom, not just its chemical label.
            t1 = structure.species[i1]
            structure[int(i1)] = structure.species[i2]
            structure[int(i2)] = t1
            if moments is not None:
                mm = list(structure.site_properties["magmom"])
                mm[i1], mm[i2] = mm[i2], mm[i1]
                structure.add_site_property("magmom", mm)
            structure = structure.get_sorted_structure()

        # Write new structure
        self._last_prepared_structure = structure
        self._write_structure_maybe_spin(structure, os.path.join(self.run_dir, "POSCAR"))
        if moments is not None:
            # Every MC step is an independent ISTART=0 SCF (see finalize_step),
            # so INCAR's MAGMOM must be refreshed to match the atoms actually
            # sitting in run_dir/POSCAR right now, not whatever it was at
            # job start.
            update_incar_magmom(
                os.path.join(self.run_dir, "INCAR"),
                format_magmom(structure.site_properties["magmom"]),
            )
        if restart:
            self._write_structure_maybe_spin(structure, os.path.join(self.run_dir, "accepted_POSCAR"))
            self._accepted_structure = structure

    _MCLOG_HEADER = (
        "# step accepted_energy perturbed_energy dE probability random "
        "accepted cum_accept_ratio runtime_s saved\n"
    )

    def _ensure_mclog_header(self, mclog_path):
        if not os.path.exists(mclog_path):
            with open(mclog_path, "w") as f:
                f.write(self._MCLOG_HEADER)

    def _cumulative_accept_stats(self, mclog_path, this_accept):
        """Cumulative (ratio, n_accepted, n_proposed) over all *proposed*
        swap steps logged so far (restart/init lines are not proposals and
        are excluded), including the current step. Recomputed from the log
        file itself each call rather than kept as in-memory state, so it is
        exact after a resume in a fresh process with no extra bookkeeping."""
        n_accepted, n_total = 0, 0
        if os.path.exists(mclog_path):
            with open(mclog_path) as f:
                for line in f:
                    if line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) < 7 or parts[4] == "NA":
                        continue  # restart/init line, or old-format log — not a proposal
                    n_total += 1
                    if parts[6] == "1":
                        n_accepted += 1
        n_total += 1
        if this_accept:
            n_accepted += 1
        return n_accepted / n_total, n_accepted, n_total

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
        mclog_path = os.path.join(self.save_dir, "MClog")
        self._ensure_mclog_header(mclog_path)

        if restart:
            # For restart steps, always accept — there's no prior state to
            # compare against, so dE/probability/random/ratio don't apply.
            with open(os.path.join(self.run_dir, "accepted_energy"), 'w') as f:
                f.write(str(energy_flip))
            # Save a snapshot too, so a later resume from this MClog line can
            # always reload save_dir/POSCAR_{step} (mirrors the non-restart path below).
            # self._accepted_structure was just set by prepare_step, no need to re-read from disk.
            self._write_structure_maybe_spin(self._accepted_structure, os.path.join(self.save_dir, f"POSCAR_{step}"))
            with open(mclog_path, "a") as f:
                f.write(f"{step} {energy_flip} NA NA NA NA 1 NA {runtime_str} 1\n")
            return True

        # Read current accepted energy
        with open(os.path.join(self.run_dir, "accepted_energy"), 'r') as f:
            current_energy = float(f.readline())
        previous_energy = current_energy
        dE = energy_flip - previous_energy

        # Metropolis acceptance criterion. Clamp the exponent at 0 to avoid an
        # overflow warning from np.exp on large positive deltas (result is
        # discarded by min(1, ...) anyway).
        delta = -dE / (self.kb * self.temperature)
        probability = 1.0 if delta >= 0 else np.exp(delta)

        random_draw = np.random.random()
        accept = random_draw < probability
        if accept:
            current_energy = energy_flip
            # self._last_prepared_structure is the exact structure just written
            # to run_dir/POSCAR by prepare_step, no need to re-read from disk.
            structure = self._last_prepared_structure
            self._write_structure_maybe_spin(structure, os.path.join(self.run_dir, "accepted_POSCAR"))
            self._accepted_structure = structure
            with open(os.path.join(self.run_dir, "accepted_energy"), 'w') as f:
                f.write(str(energy_flip))

        # Save a structure snapshot only every save_freq steps (expensive);
        # MClog itself is logged every step regardless (cheap, and needed for
        # an exact cumulative acceptance ratio).
        saved = 1 if step % save_freq == 0 else 0
        if saved:
            self._write_structure_maybe_spin(self._accepted_structure, os.path.join(self.save_dir, f"POSCAR_{step}"))

        ratio, _, _ = self._cumulative_accept_stats(mclog_path, accept)
        with open(mclog_path, "a") as f:
            f.write(f"{step} {current_energy} {energy_flip} {dE:.6f} {probability:.6f} "
                    f"{random_draw:.6f} {int(accept)} {ratio:.4f} {runtime_str} {saved}\n")

        return accept

    def restore_accepted_energy(self, energy):
        """Write a previously accepted energy value into run_dir (used when resuming)"""
        with open(os.path.join(self.run_dir, "accepted_energy"), 'w') as f:
            f.write(str(energy))

    @staticmethod
    def read_last_step(mclog_path):
        """Read the last resumable step (one with a saved structure snapshot)
        and its accepted energy from MClog. Falls back to treating every
        line as resumable for older (pre-"saved"-column) log files."""
        with open(mclog_path, 'r') as f:
            lines = [l for l in f if l.strip() and not l.startswith("#")]
        for line in reversed(lines):
            parts = line.split()
            if len(parts) >= 10 and parts[9] != "1":
                continue  # no structure snapshot was saved for this step
            return int(parts[0]), float(parts[1])
        raise RuntimeError(f"No resumable step (with a saved snapshot) found in {mclog_path}")

    @staticmethod
    def truncate_mclog(mclog_path, istart):
        """Drop MClog rows for any step after `istart`.

        Because a structure snapshot is only saved every save_freq steps,
        resuming can only continue from the last step that has one — steps
        logged after that point but before the job stopped represent an
        abandoned trajectory branch (their proposals were never kept on
        disk). Call this once right after read_last_step(), before resuming,
        so later cumulative-acceptance-ratio calculations don't silently
        include that abandoned branch."""
        with open(mclog_path) as f:
            lines = f.readlines()
        keep = []
        for line in lines:
            if line.startswith("#") or not line.strip():
                keep.append(line)
                continue
            if int(line.split()[0]) <= istart:
                keep.append(line)
        with open(mclog_path, "w") as f:
            f.writelines(keep) 
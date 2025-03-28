"""
DFTMonteCarlo package for running Monte Carlo simulations with VASP.
"""

from .mc_utils import MCRunner

__version__ = "0.1.0"
__author__ = "Yifan Cao"
__email__ = "yifanc@mit.com"

# Export main class
__all__ = ["MCRunner"] 
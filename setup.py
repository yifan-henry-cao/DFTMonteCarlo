from setuptools import setup, find_packages

setup(
    name="dft_monte_carlo",
    version="0.1.0",
    description="Monte Carlo simulation with DFT energy calculations",
    author="Yifan Cao",
    author_email="yifanc@mit.com",
    packages=find_packages(include=['dftmc', 'dftmc.*']),
    install_requires=[
        "pymatgen>=2022.2.10",
        "numpy>=1.20.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=22.0.0",
            "pylint>=2.8.0",
        ],
        "plot": [
            "matplotlib>=3.4.0",
        ],
    },
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'dftmc=dftmc.DFTMC:main',
        ],
    },
) 
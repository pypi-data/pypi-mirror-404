# Siegert Scatter

Compute radial (partial-wave) Schrödinger scattering using the Siegert pseudostate (SPS) method. This library produces S-matrices, cross sections, Wigner time delays, and scattering lengths for user-defined potentials.

**This library is an implementation of the Siegert pseudostate method for quantum scattering as described in:**

> Batishchev, P. A. & Tolstikhin, O. I. (2007). *Siegert pseudostate formulation of scattering theory: Nonzero angular momenta in the one-channel case.* Physical Review A, 75, 062704.  
> [https://doi.org/10.1103/PhysRevA.75.062704](https://journals.aps.org/pra/abstract/10.1103/PhysRevA.75.062704)

## Installation

```bash
pip install siegert-scatter
```

## Usage

See the [K-He example](#example-k-he-spin-exchange-scattering) below for a complete real-world use case.

## Command-Line Interface

The package provides a CLI for computing scattering from tabular potential files.

### Basic Usage

```bash
siegert-scatter --help
siegert-scatter scatter --help

siegert-scatter scatter potential.dat

siegert-scatter scatter potential.dat -N 100 -a 15 -l 10 --e-max 5.0 -v
```

### Input Format

The potential file should contain two columns: r (Bohr) and V (Hartree).
Lines starting with `#` are treated as comments.

```
# r(Bohr)  V(Hartree)
0.5        -10.0
1.0        -5.0
2.0        -1.0
```

### Output Files

The CLI produces two output files:
- `{prefix}.npz`: NumPy archive with S-matrix, cross sections, time delays, etc.
- `{prefix}.json`: Summary metadata with parameters, version, and timestamp

## Example: K-He Spin-Exchange Scattering

For a complete real-world example, see [`scripts/KHe-example/run_everything.py`](scripts/KHe-example/run_everything.py), which computes spin-exchange cross-sections for potassium–helium (K-He) collisions.

> **Note**: The K-He example is a specialized workflow that is not part of the packaged CLI. It requires additional dependencies and input data. See the [example README](scripts/KHe-example/README.md) for details.

This example demonstrates the library's capabilities in the context of the following work:

> Tsinovoy, A., Katz, O., Landau, A. & Moiseyev, N. (2022). *Enhanced Coupling of Electron and Nuclear Spins by Quantum Tunneling Resonances.* Physical Review Letters, 128, 013401.  
> [https://doi.org/10.1103/PhysRevLett.128.013401](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.128.013401)

## How to cite

If you use this software in your research, please cite it.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18190655.svg)](https://doi.org/10.5281/zenodo.18190655)

See the [`CITATION.cff`](CITATION.cff) file for citation metadata compatible with GitHub's citation feature.

## License

MIT License. See [LICENSE](LICENSE) for details.

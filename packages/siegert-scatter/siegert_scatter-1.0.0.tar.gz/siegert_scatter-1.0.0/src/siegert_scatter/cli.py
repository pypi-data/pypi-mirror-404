"""Command-line interface for siegert-scatter."""

import argparse
import json
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np

from .cross_section import _InterpolatedPotential, calc_cross_section


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the siegert-scatter CLI.

    Parameters
    ----------
    argv : list[str] | None
        Command-line arguments. If None, uses sys.argv[1:].

    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        prog="siegert-scatter",
        description=(
            "Compute quantum scattering using the Siegert pseudostate method. "
            "Produces S-matrices, cross sections, time delays, and scattering lengths."
        ),
    )

    # Global version flag
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('siegert-scatter')}",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ========================================================================
    # scatter subcommand
    # ========================================================================
    scatter_parser = subparsers.add_parser(
        "scatter",
        help="Compute scattering for a tabular potential",
        description=(
            "Compute scattering observables for a tabular potential file using "
            "the Siegert pseudostate (SPS) method.\n\n"
            "POTENTIAL FILE FORMAT:\n"
            "  - Two columns: r (Bohr), V (Hartree)\n"
            "  - Whitespace or comma-separated\n"
            "  - Lines starting with # are treated as comments\n"
            "  - Example:\n"
            "      # r(Bohr)  V(Hartree)\n"
            "      0.1        -10.5\n"
            "      0.2        -8.3\n\n"
            "OUTPUT FILES:\n"
            "  - {prefix}.npz: NumPy archive with arrays (E_vec, S_l, sigma_l, etc.)\n"
            "  - {prefix}.json: Summary metadata (parameters, version, timestamp)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Positional argument
    scatter_parser.add_argument(
        "potential_file",
        help="Path to tabular potential file (two columns: r, V)",
    )

    # Basis and cutoff parameters
    scatter_parser.add_argument(
        "-N",
        "--basis-size",
        type=int,
        default=50,
        metavar="N",
        help="Number of basis functions (default: 50)",
    )
    scatter_parser.add_argument(
        "-a",
        "--cutoff",
        type=float,
        default=10.0,
        metavar="a",
        help="Potential cutoff radius in Bohr (default: 10.0)",
    )
    scatter_parser.add_argument(
        "-l",
        "--l-max",
        type=int,
        default=5,
        metavar="L",
        help="Maximum angular momentum quantum number (default: 5)",
    )

    # Energy grid parameters
    scatter_parser.add_argument(
        "--e-min",
        type=float,
        default=1e-6,
        metavar="E",
        help="Minimum energy in Hartree (default: 1e-6)",
    )
    scatter_parser.add_argument(
        "--e-max",
        type=float,
        default=10.0,
        metavar="E",
        help="Maximum energy in Hartree (default: 10.0)",
    )
    scatter_parser.add_argument(
        "--e-steps",
        type=int,
        default=1000,
        metavar="N",
        help="Number of energy steps (default: 1000)",
    )

    # Pole augmentation
    scatter_parser.add_argument(
        "--dgamma",
        type=float,
        default=0.0,
        metavar="Γ",
        help="Width parameter for pole augmentation in Hartree (default: 0.0)",
    )

    # Grid refinement
    scatter_parser.add_argument(
        "--no-adaptive-grid",
        action="store_true",
        help="Disable adaptive grid refinement near resonances",
    )

    # Parallelization
    scatter_parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        metavar="N",
        help="Maximum parallel workers (default: all available CPUs)",
    )

    # Output and verbosity
    scatter_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        metavar="PREFIX",
        help=(
            "Output file prefix (default: derived from input filename). "
            "Produces {PREFIX}.npz and {PREFIX}.json"
        ),
    )
    scatter_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    # Parse arguments
    args = parser.parse_args(argv)

    # If no command specified, print help
    if args.command is None:
        parser.print_help()
        return 0

    # Dispatch to subcommand handler
    if args.command == "scatter":
        return _scatter_handler(args)

    # Should never reach here
    return 1


def _scatter_handler(args: argparse.Namespace) -> int:
    """Handle the 'scatter' subcommand."""
    potential_path = Path(args.potential_file)
    if not potential_path.exists():
        print(
            f"Error: Potential file not found: {args.potential_file}", file=sys.stderr
        )
        return 1

    try:
        r_data, V_data = _load_potential(args.potential_file)
    except ValueError as e:
        print(f"Error loading potential file: {e}", file=sys.stderr)
        return 1

    potential_fn = _InterpolatedPotential(r_data, V_data)

    E_vec = np.linspace(args.e_min, args.e_max, args.e_steps)

    if args.verbose:
        print(f"Computing scattering for: {args.potential_file}")
        print(f"  Basis size N = {args.basis_size}")
        print(f"  Cutoff radius a = {args.cutoff} Bohr")
        print(f"  Max angular momentum l_max = {args.l_max}")
        print(
            f"  Energy range: {args.e_min} - {args.e_max} Hartree ({args.e_steps} steps)"
        )
        print(f"  dGamma = {args.dgamma}")
        print(f"  Adaptive grid: {not args.no_adaptive_grid}")

    result = calc_cross_section(
        potential_fn,
        args.basis_size,
        args.cutoff,
        args.l_max,
        E_vec,
        dGamma=args.dgamma,
        verbose=args.verbose,
        adaptive_grid=not args.no_adaptive_grid,
        max_workers=args.max_workers,
    )

    output_prefix = args.output if args.output is not None else str(potential_path.stem)
    npz_path = f"{output_prefix}.npz"
    json_path = f"{output_prefix}.json"

    npz_data: dict[str, np.ndarray] = {
        "E_vec": result.E_vec,
        "E_vec_input": result.E_vec_input,
        "S_l": result.S_l,
        "sigma_l": result.sigma_l,
        "tau_l": result.tau_l,
        "alpha": np.atleast_1d(result.alpha),
        "l_vec": result.l_vec,
    }
    for ell, k_n in enumerate(result.k_n_l):
        npz_data[f"k_n_l_{ell}"] = k_n

    np.savez(npz_path, allow_pickle=True, **npz_data)

    json_summary = {
        "command": " ".join(sys.argv),
        "input_file": str(potential_path.resolve()),
        "output_files": {
            "npz": str(Path(npz_path).resolve()),
            "json": str(Path(json_path).resolve()),
        },
        "parameters": {
            "N": args.basis_size,
            "a": args.cutoff,
            "l_max": args.l_max,
            "dGamma": args.dgamma,
            "adaptive_grid": not args.no_adaptive_grid,
            "max_workers": args.max_workers,
            "E_min": args.e_min,
            "E_max": args.e_max,
            "E_steps": args.e_steps,
        },
        "version": version("siegert-scatter"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_E": len(result.E_vec),
        "n_l": len(result.l_vec),
        "alpha": float(result.alpha),
    }

    with open(json_path, "w") as f:
        json.dump(json_summary, f, indent=2)

    if args.verbose:
        print("\nOutput written to:")
        print(f"  {npz_path}")
        print(f"  {json_path}")
        print(f"Scattering length (alpha) = {result.alpha:.6e} Bohr")

    return 0


def _load_potential(path: str) -> tuple[np.ndarray, np.ndarray]:
    """Load tabular potential file with r (Bohr) and V (Hartree) columns."""
    r_values: list[float] = []
    v_values: list[float] = []

    with open(path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            line = line.replace(",", " ")
            parts = line.split()

            if len(parts) < 2:
                raise ValueError(
                    f"Line {line_num}: expected 2 columns (r, V), got {len(parts)}"
                )

            try:
                r = float(parts[0])
                v = float(parts[1])
            except ValueError as e:
                raise ValueError(f"Line {line_num}: cannot parse values: {e}") from e

            r_values.append(r)
            v_values.append(v)

    if len(r_values) == 0:
        raise ValueError("No data found in potential file")

    return np.array(r_values), np.array(v_values)

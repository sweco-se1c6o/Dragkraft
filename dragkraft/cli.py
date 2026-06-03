from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from dragkraft.io.outputs import write_simulation_outputs
from dragkraft.simulation.orchestrator import simulate_workbook
from dragkraft.vehicles.legacy_cases import default_nyprofil_scenario, legacy_freight_20


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args)
    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dragkraft")
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="Run a legacy Dragkraft workbook")
    run.add_argument("workbook", type=Path)
    run.add_argument("--sheet", default="NyProfil")
    run.add_argument("--train", choices=["legacy-freight-20"], default="legacy-freight-20")
    run.add_argument("--extra-wagons", type=int, default=21)
    run.add_argument("--max-speed-kmh", type=float, default=40.0)
    direction = run.add_mutually_exclusive_group()
    direction.add_argument("--flip", action="store_true", dest="flip_profiles")
    direction.add_argument("--no-flip", action="store_false", dest="flip_profiles")
    run.set_defaults(flip_profiles=None)
    run.add_argument("--out", type=Path, required=True)
    return parser


def _run(args: argparse.Namespace) -> int:
    settings = default_nyprofil_scenario()
    settings = replace(
        settings,
        sheet_name=args.sheet,
        train_name=args.train,
        extra_wagon_count=args.extra_wagons,
        speed_override_kmh=args.max_speed_kmh,
        flip_profiles=(
            settings.flip_profiles
            if args.flip_profiles is None
            else bool(args.flip_profiles)
        ),
    )
    train = legacy_freight_20(extra_wagons=args.extra_wagons)
    result = simulate_workbook(
        workbook_path=args.workbook,
        train=train,
        settings=settings,
    )
    write_simulation_outputs(result=result, output_dir=args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

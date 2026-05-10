#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SELECT_SCRIPT = ROOT / "select_operating_week.py"
VALIDATE_SCRIPT = ROOT / "validate_films.py"
CHECK_SCRIPT = ROOT / "check-films.py"


def run_step(command, label, allowed_exit_codes=None):
    allowed_exit_codes = allowed_exit_codes or {0}
    print(f"[{label}] {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode not in allowed_exit_codes:
        print(f"[{label}] failed with exit code {result.returncode}")
        return result.returncode
    return 0


def main():
    parser = argparse.ArgumentParser(description="Refresh Wednesday operating week and weekly state sequentially.")
    parser.add_argument("--today", help="Override local date in YYYY-MM-DD format.")
    parser.add_argument("--updated-by", default="codex")
    parser.add_argument(
        "--mode",
        choices=["active", "prerelease"],
        default="prerelease",
        help="Pick the upcoming prerelease slate by default for Wednesday work.",
    )
    parser.add_argument("--skip-check", action="store_true", help="Skip final check-films summary.")
    args = parser.parse_args()

    select_cmd = [sys.executable, str(SELECT_SCRIPT), "--updated-by", args.updated_by, "--mode", args.mode]
    if args.today:
        select_cmd.extend(["--today", args.today])

    steps = [
        (select_cmd, "select_operating_week", {0}),
        ([sys.executable, str(VALIDATE_SCRIPT)], "validate_films", {0}),
    ]

    if not args.skip_check:
        steps.append(([sys.executable, str(CHECK_SCRIPT)], "check_films", {0, 1}))

    for command, label, allowed_exit_codes in steps:
        exit_code = run_step(command, label, allowed_exit_codes)
        if exit_code != 0:
            return exit_code

    print("Wednesday state refreshed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

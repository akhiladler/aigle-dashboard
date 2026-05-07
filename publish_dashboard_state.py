#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent
PUBLISH_FILES = [
    "films.json",
    "films_schedule.json",
    "operating_week.json",
    "weekly_state.json",
    "refresh_wednesday_state.py",
    "update_youtube_signals.py",
]


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def status_lines() -> list[str]:
    proc = run_git("status", "--porcelain", check=True)
    return [line for line in proc.stdout.splitlines() if line.strip()]


def has_repo_surgery_risk() -> tuple[bool, str]:
    git_dir = ROOT / ".git"
    risk_markers = [
        git_dir / "MERGE_HEAD",
        git_dir / "REBASE_HEAD",
        git_dir / "CHERRY_PICK_HEAD",
    ]
    for marker in risk_markers:
        if marker.exists():
            return True, f"Repository operation in progress: {marker.name}"
    return False, ""


def has_conflict_markers() -> tuple[bool, str]:
    for rel in PUBLISH_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "<<<<<<<" in text or "=======" in text or ">>>>>>>" in text:
            return True, f"Conflict markers found in {rel}"
    return False, ""


def split_status(lines: list[str]) -> tuple[list[str], list[str]]:
    publish = []
    unrelated = []
    for line in lines:
        rel = line[3:]
        if rel in PUBLISH_FILES:
            publish.append(line)
        else:
            unrelated.append(line)
    return publish, unrelated


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_state_alignment() -> tuple[bool, str, dict[str, str]]:
    operating_path = ROOT / "operating_week.json"
    weekly_state_path = ROOT / "weekly_state.json"

    receipts = {
        "OPERATING_WEEK_LABEL": "unknown",
        "OPERATING_WEEK_START": "unknown",
        "OPERATING_UPDATED_AT": "unknown",
        "WEEKLY_STATE_LABEL": "unknown",
        "WEEKLY_STATE_START": "unknown",
        "WEEKLY_STATE_GENERATED_AT": "unknown",
        "WEEKLY_STATE_READY_FOR_PUBLISH": "unknown",
    }

    if not operating_path.exists():
        return False, "operating_week.json missing", receipts
    if not weekly_state_path.exists():
        return False, "weekly_state.json missing", receipts

    try:
        operating = load_json(operating_path)
    except Exception as exc:
        return False, f"Failed to parse operating_week.json: {exc}", receipts

    try:
        weekly_state = load_json(weekly_state_path)
    except Exception as exc:
        return False, f"Failed to parse weekly_state.json: {exc}", receipts

    operating_titles = operating.get("films_releasing") or []
    weekly_titles = weekly_state.get("films_in_scope") or []

    receipts.update({
        "OPERATING_WEEK_LABEL": str(operating.get("week_label", "unknown")),
        "OPERATING_WEEK_START": str(operating.get("week_start", "unknown")),
        "OPERATING_UPDATED_AT": str(operating.get("updated_at", "unknown")),
        "WEEKLY_STATE_LABEL": str(weekly_state.get("week_label", "unknown")),
        "WEEKLY_STATE_START": str(weekly_state.get("week_start", "unknown")),
        "WEEKLY_STATE_GENERATED_AT": str(weekly_state.get("generated_at", "unknown")),
        "WEEKLY_STATE_READY_FOR_PUBLISH": str(bool(weekly_state.get("ready_for_publish"))).lower(),
    })

    if operating.get("week_label") != weekly_state.get("week_label"):
        return False, "week_label mismatch between operating_week.json and weekly_state.json", receipts
    if operating.get("week_start") != weekly_state.get("week_start"):
        return False, "week_start mismatch between operating_week.json and weekly_state.json", receipts
    if operating_titles != weekly_titles:
        return False, "films_in_scope mismatch between operating_week.json and weekly_state.json", receipts
    if weekly_state.get("ready_for_publish") is not True:
        return False, "weekly_state.json is not publish-ready", receipts

    return True, "", receipts


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Stage, commit, and optionally push canonical Aigle dashboard state.")
    parser.add_argument("--message", help="Commit message to use if changes exist.")
    parser.add_argument("--push", action="store_true", help="Push after commit.")
    parser.add_argument("--dry-run", action="store_true", help="Report publish decision without staging or writing.")
    parser.add_argument("--repo-root", default=str(DEFAULT_ROOT), help="Path to the actual dashboard git repo.")
    args = parser.parse_args()

    ROOT = Path(args.repo_root).resolve()

    if not args.dry_run and not args.message:
        parser.error("--message is required unless --dry-run is used")

    if not (ROOT / ".git").exists():
        print(f"BLOCKED | {ROOT} is not a git repository root")
        return 2

    risky, reason = has_repo_surgery_risk()
    if risky:
        print(f"BLOCKED | {reason}")
        return 2

    conflicted, reason = has_conflict_markers()
    if conflicted:
        print(f"BLOCKED | {reason}")
        return 2

    lines = status_lines()
    publish_lines, unrelated_lines = split_status(lines)

    canonical_dirty = [line[3:] for line in publish_lines]
    unrelated_dirty = [line[3:] for line in unrelated_lines]
    state_ok, state_blocker, receipts = validate_state_alignment()

    if args.dry_run:
        print(f"REPO_ROOT | {ROOT}")
        for key, value in receipts.items():
            print(f"{key} | {value}")
        print("CANONICAL_PUBLISH_FILES | " + (", ".join(canonical_dirty) if canonical_dirty else "clean"))
        print("UNRELATED_DIRTY_FILES | " + (", ".join(unrelated_dirty) if unrelated_dirty else "none"))
        if not state_ok:
            print("DECISION | block")
            print(f"BLOCKER | {state_blocker}")
        else:
            print("DECISION | proceed")
            print("BLOCKER | none")
        return 0

    if not state_ok:
        print(f"BLOCKED | {state_blocker}")
        return 2

    if not publish_lines:
        print("NO_CHANGES | No canonical dashboard state changes to publish.")
        if unrelated_lines:
            print("UNRELATED_DIRTY |")
            for line in unrelated_lines:
                print(line)
        return 0

    run_git("add", *PUBLISH_FILES)

    staged = run_git("diff", "--cached", "--name-only").stdout.splitlines()
    staged_publish = [name for name in staged if name in PUBLISH_FILES]
    if not staged_publish:
        print("NO_STAGED_PUBLISH_FILES | Canonical files did not stage.")
        return 1

    if unrelated_lines:
        print("UNRELATED_DIRTY |")
        for line in unrelated_lines:
            print(line)

    print("STAGED |")
    for name in staged_publish:
        print(name)

    run_git("commit", "-m", args.message)
    print(f"COMMITTED | {args.message}")

    if args.push:
        run_git("push", "origin", "master")
        print("PUSHED | origin/master")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

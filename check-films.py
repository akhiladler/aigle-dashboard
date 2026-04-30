#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEEKLY_STATE_PATH = ROOT / 'weekly_state.json'


def load_state():
    return json.loads(WEEKLY_STATE_PATH.read_text(encoding='utf-8'))


def print_group(label, items):
    if not items:
        return
    print(f'{label}:')
    for item in items:
        print(f"- {item['title']}: {', '.join(item['fields'])}")


def main():
    if not WEEKLY_STATE_PATH.exists():
        print('weekly_state.json missing. Run validate_films.py first.')
        return 1

    state = load_state()
    print(f"Week: {state.get('week_label')} ({state.get('week_start')})")
    print(state.get('operator_summary', 'No summary available.'))
    print_group('Missing human inputs', state.get('missing_human_inputs', []))
    print_group('Missing autofillable inputs', state.get('missing_autofillable_inputs', []))
    print_group('Missing audit inputs', state.get('missing_audit_inputs', []))

    anomalies = state.get('anomalies', [])
    if anomalies:
        print('Anomalies:')
        for item in anomalies:
            print(f"- {item['title']}: {', '.join(item['issues'])}")

    return 0 if state.get('ready_for_publish') else 1


if __name__ == '__main__':
    sys.exit(main())

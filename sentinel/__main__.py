import argparse
import json
import sys
from pathlib import Path
from .core import assess, atomic_json, read_json, validate_schema
from .report import render_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare a schema with its approved baseline.")
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot", help="Create an approved baseline from a JSON schema")
    snapshot.add_argument("--schema", required=True)
    snapshot.add_argument("--baseline", required=True)
    snapshot.add_argument("--overwrite", action="store_true")
    check = commands.add_parser("check", help="Compare and persist incident state")
    check.add_argument("--baseline", required=True)
    check.add_argument("--schema", required=True)
    check.add_argument("--dataset", required=True)
    check.add_argument("--state", default=".sentinel/state.json")
    check.add_argument("--output", default="reports/latest.json")
    check.add_argument("--html", default="reports/latest.html")
    check.add_argument("--lineage", help="JSON array of upstream asset names")
    check.add_argument("--fail-on-breaking", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            if Path(args.baseline).exists() and not args.overwrite:
                raise ValueError("Baseline exists. Use --overwrite after reviewing the change.")
            atomic_json(args.baseline, validate_schema(read_json(args.schema)))
            print(f"Baseline saved to {args.baseline}")
            return 0
        # Prevent accidental overwriting of an input or one output by another.
        inputs = [args.baseline, args.schema] + ([args.lineage] if args.lineage else [])
        outputs = [args.state, args.output, args.html]
        resolved = [Path(x).resolve() for x in outputs]
        if len(set(resolved)) != len(outputs) or set(resolved) & {Path(x).resolve() for x in inputs}:
            raise ValueError("Input and output paths must be distinct.")
        state = read_json(args.state) if Path(args.state).exists() else {}
        upstreams = read_json(args.lineage) if args.lineage else None
        if upstreams is not None and (not isinstance(upstreams, list) or
                                     not all(isinstance(x, str) for x in upstreams)):
            raise ValueError("Lineage must be a JSON array of strings.")
        report = assess(args.dataset, read_json(args.baseline), read_json(args.schema), state, upstreams)
        render_report(report, args.html)
        atomic_json(args.output, report)
        atomic_json(args.state, state)
        print(f"{report['status'].upper()}: {len(report['changes'])} changes; {report['resolved']} resolved")
        print(f"Report: {args.html}")
        return 2 if args.fail_on_breaking and report['status'] == 'breaking' else 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

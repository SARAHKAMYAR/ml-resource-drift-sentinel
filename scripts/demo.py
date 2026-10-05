"""Generate a deterministic fixture report and exercise the incident lifecycle."""
import copy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sentinel.core import assess, atomic_json, read_json
from sentinel.report import render_report

ROOT = Path(__file__).resolve().parents[1]
baseline = read_json(ROOT / "examples/baseline.json")
current = read_json(ROOT / "examples/current.json")
upstreams = read_json(ROOT / "examples/upstreams.json")
state = {}
stages = [("Baseline", baseline), ("First drift", current), ("Repeated check", current),
          ("Recovery", baseline), ("Drift returns", current)]
history = []
for index, (name, schema) in enumerate(stages):
    report = assess("demo.customers", baseline, schema, state, upstreams,
                    timestamp=f"2026-01-15T{9+index:02d}:00:00+00:00")
    history.append(dict(stage=name, changes=len(report["changes"]),
                        opened=sum(c["newly_opened"] for c in report["changes"]),
                        resolved=report["resolved"]))
    if index == 1:
        demo = copy.deepcopy(report)
demo["demo"] = True
demo["fixture_note"] = "Synthetic schema changes; upstream names are illustrative."
atomic_json(ROOT / "docs/assets/demo-report.json", demo)
atomic_json(ROOT / "docs/assets/demo-history.json", history)
render_report(demo, ROOT / "docs/assets/demo-report.html")
print("Demo generated: docs/assets/demo-report.html")
print("Lifecycle: 5 opened → 0 opened → 5 resolved → 5 reopened")

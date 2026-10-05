"""Pure comparison logic and single-writer incident persistence."""
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_schema(schema):
    if not isinstance(schema, dict) or not all(
        isinstance(k, str) and k and isinstance(v, str) and v.strip()
        for k, v in schema.items()
    ):
        raise ValueError("Schema must map nonempty field names to nonempty type strings.")
    return schema


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         delete=False) as stream:
            temporary = stream.name
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def compare(baseline, current):
    validate_schema(baseline)
    validate_schema(current)
    changes = []
    for field in sorted(baseline.keys() | current.keys()):
        before, after = baseline.get(field), current.get(field)
        if before is None:
            kind, severity = "added", "info"
        elif after is None:
            kind, severity = "removed", "high"
        elif before.strip().upper() != after.strip().upper():
            kind, severity = "type_changed", "high"
        else:
            continue
        changes.append(dict(field=field, kind=kind, severity=severity,
                            before=before, after=after))
    return changes


def assess(dataset, baseline, current, state, upstreams=None, timestamp=None):
    """Count incident openings, not repeated observations of an active incident.

    History is scoped to dataset AND baseline. A changed baseline starts a new scope.
    """
    changes = compare(baseline, current)
    scope = fingerprint({"dataset": dataset, "baseline": baseline})
    if state.get("version", 1) != 1:
        raise ValueError("Unsupported state version")
    state.setdefault("version", 1)
    memory = state.setdefault("scopes", {}).setdefault(scope, {"active": [], "counts": {}})
    active = set(memory["active"])
    now = timestamp or datetime.now(timezone.utc).isoformat()
    new_active = []
    for change in changes:
        key = fingerprint(change)
        new_active.append(key)
        newly_opened = key not in active
        if newly_opened:
            memory["counts"][key] = memory["counts"].get(key, 0) + 1
        change.update(occurrences=memory["counts"][key], newly_opened=newly_opened)
    resolved = len(active - set(new_active))
    memory["active"] = new_active
    breaking = sum(c["severity"] == "high" for c in changes)
    status = "breaking" if breaking else "review" if changes else "healthy"
    return dict(version=1, dataset=dataset, checked_at=now, status=status,
                baseline_fields=len(baseline), current_fields=len(current),
                changes=changes, resolved=resolved, upstreams=upstreams,
                lineage_note="Upstream assets are investigation leads; they do not establish causality.",
                recommendation=("Review removed fields and type changes before the next downstream run."
                                if breaking else "Review additions against consumer contracts."
                                if changes else "No schema changes relative to the baseline."))

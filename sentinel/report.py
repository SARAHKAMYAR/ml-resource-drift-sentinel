"""Portable HTML report. Escapes metadata and needs no external scripts or fonts."""
from html import escape
from pathlib import Path


def render_report(report, path):
    def e(value):
        return escape(str(value if value is not None else "—"), quote=True)
    counts = {kind: sum(c["kind"] == kind for c in report["changes"])
              for kind in ("removed", "type_changed", "added")}
    colors = {"removed": "#fb7185", "type_changed": "#fbbf24", "added": "#38bdf8"}
    maximum = max(counts.values(), default=1) or 1
    bars = "".join(f'<text x="0" y="{30+i*55}" fill="#dbeafe">{kind.replace("_", " ")}</text>'
                   f'<rect x="140" y="{12+i*55}" width="{count/maximum*360}" height="26" rx="5" fill="{colors[kind]}"/>'
                   f'<text x="{150+count/maximum*360}" y="{31+i*55}" fill="white">{count}</text>'
                   for i,(kind,count) in enumerate(counts.items()))
    rows = "".join(f'<tr><td>{e(c["field"])}</td><td>{e(c["kind"])}</td>'
                   f'<td>{e(c["before"])}</td><td>{e(c["after"])}</td>'
                   f'<td>{e(c["severity"])}</td><td>{c["occurrences"]}</td>'
                   f'<td>{"Opened" if c["newly_opened"] else "Still active"}</td></tr>'
                   for c in report["changes"])
    upstreams = report.get("upstreams")
    context = ("Lineage was not supplied." if upstreams is None else
               "No upstream assets were supplied." if not upstreams else
               ", ".join(upstreams))
    fixture = "<p><strong>Synthetic demo</strong> · Schema changes and upstream names are illustrative.</p>" if report.get("demo") else ""
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Schema report · Drift Sentinel</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#0b1220;color:#e2e8f0;font:16px system-ui,sans-serif}}
main{{max-width:1120px;margin:auto;padding:48px 24px}}.eyebrow{{color:#38bdf8;letter-spacing:3px;font-size:12px}}
h1{{font-size:42px;letter-spacing:-1px;margin:14px 0}}p{{color:#aebed4;line-height:1.7}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:28px 0}}
.card,section{{background:#121e31;border:1px solid #26354b;border-radius:14px;padding:22px}}
.card strong{{display:block;font-size:28px;margin-top:10px}}.card span{{color:#aebed4}}
section{{margin-top:20px}}h2{{font-size:20px}}.scroll{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{text-align:left;padding:14px 10px;border-bottom:1px solid #26354b}}
th{{color:#aebed4}}svg{{max-width:600px;width:100%;height:auto}}
code{{overflow-wrap:anywhere}}footer{{margin-top:28px;color:#aebed4;font-size:13px}}
@media(max-width:650px){{.cards{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:32px}}}}
</style><main><div class="eyebrow">ML RESOURCE DRIFT SENTINEL / SCHEMA MONITOR</div>
<h1>See what changed. Keep the context.</h1>{fixture}<p><code>{e(report['dataset'])}</code><br>Checked {e(report['checked_at'])}</p>
<div class="cards"><div class="card"><span>Status</span><strong>{e(report['status'].title())}</strong></div>
<div class="card"><span>Baseline fields</span><strong>{report['baseline_fields']}</strong></div>
<div class="card"><span>Current fields</span><strong>{report['current_fields']}</strong></div>
<div class="card"><span>Changes</span><strong>{len(report['changes'])}</strong></div></div>
<section><h2>Changes by category</h2><svg viewBox="0 0 560 175" role="img" aria-label="Schema change counts: {e(counts)}">{bars}</svg>
<p>Policy: removals and type changes require review. Additions are informational.</p></section>
<section><h2>Field comparison</h2><div class="scroll"><table><thead><tr><th>Field</th><th>Change</th><th>Before</th><th>After</th><th>Severity</th><th>Incidents</th><th>This check</th></tr></thead>
<tbody>{rows or '<tr><td colspan="7">No schema changes.</td></tr>'}</tbody></table></div>
<p>Incident counts increase when a change first appears or returns after recovery, not on every check.</p></section>
<section><h2>Investigation context</h2><p>{e(context)}</p><p>{e(report['lineage_note'])}</p>
<h2>Next step</h2><p>{e(report['recommendation'])}</p></section>
<footer>Schema comparison only · This report does not measure model performance or feature distributions.</footer></main></html>"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")

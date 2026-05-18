from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


CAUTION_HTML = """
<div class="caution">
  <strong>Important caution:</strong>
  Real TRIBE output from synthetic resume-reading events. No human was scanned.
  This is not a hiring prediction. Section-level aggregation is a proxy.
</div>
"""


PROXY_DEFINITIONS = {
    "response_intensity": "Mean absolute predicted response magnitude summarized for a section.",
    "salience_proxy": "Relative section response intensity normalized across sections.",
    "position_normalized_salience": "A heuristic salience adjustment that reduces early-section dominance in synthetic reading timelines.",
    "cognitive_load_proxy": "A proxy combining response variability and section density/timing signals.",
    "underemphasis_proxy": "A proxy for sections that contain evidence but have lower relative salience.",
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_html(path: str | Path, title: str, body: str) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape_html(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --text: #202124;
      --muted: #5f6368;
      --border: #d9dee3;
      --bg: #f6f8fa;
      --panel: #ffffff;
      --accent: #2457a6;
      --warn-bg: #fff7df;
      --warn-border: #d79b00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      margin: 0;
      color: var(--text);
      background: var(--bg);
      line-height: 1.45;
    }}
    main {{ max-width: 1440px; margin: 0 auto; padding: 20px; }}
    h1, h2, h3 {{ line-height: 1.2; margin: 0 0 12px; }}
    h1 {{ font-size: 28px; }}
    h2 {{ font-size: 20px; margin-top: 28px; }}
    h3 {{ font-size: 16px; }}
    p {{ margin: 8px 0 12px; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 20px; background: var(--panel); }}
    th, td {{ border: 1px solid var(--border); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f6; position: sticky; top: 0; z-index: 1; }}
    code {{ background: #eef2f6; padding: 2px 4px; border-radius: 4px; }}
    pre {{ overflow-x: auto; background: #111827; color: #f9fafb; padding: 14px; border-radius: 8px; }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      background: rgba(255,255,255,.94);
      border-bottom: 1px solid var(--border);
      backdrop-filter: blur(8px);
    }}
    .topbar-inner {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 10px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      flex-wrap: wrap;
    }}
    .navlinks {{ display: flex; flex-wrap: wrap; gap: 10px; font-size: 14px; }}
    .navlinks a {{ padding: 6px 8px; border-radius: 6px; }}
    .navlinks a:hover {{ background: #eef2f6; text-decoration: none; }}
    .eyebrow {{ color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: .04em; }}
    .hero {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 16px;
    }}
    .caution {{
      border: 1px solid var(--warn-border);
      background: var(--warn-bg);
      padding: 12px;
      margin: 14px 0;
      border-radius: 8px;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }}
    .card {{
      border: 1px solid var(--border);
      padding: 14px;
      border-radius: 8px;
      background: var(--panel);
    }}
    .metric {{
      font-size: 24px;
      font-weight: 700;
      margin-top: 4px;
    }}
    .muted {{ color: var(--muted); }}
    .table-wrap {{ max-height: 520px; overflow: auto; border: 1px solid var(--border); border-radius: 8px; background: var(--panel); }}
    .table-wrap table {{ margin: 0; }}
    .chart-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      margin: 16px 0;
      overflow: hidden;
    }}
    .plot {{ width: 100%; height: min(560px, 72vh); }}
    .preview-img {{ display: block; width: 100%; max-height: 460px; object-fit: contain; background: #fff; border: 1px solid var(--border); border-radius: 8px; }}
    .callout {{ border-left: 4px solid var(--accent); padding: 8px 12px; background: #eef4ff; border-radius: 6px; }}
    @media (max-width: 760px) {{
      main {{ padding: 14px; }}
      h1 {{ font-size: 24px; }}
      .topbar-inner {{ padding: 8px 14px; align-items: flex-start; }}
      .plot {{ height: 440px; }}
      th, td {{ font-size: 13px; }}
    }}
  </style>
</head>
<body>
<div class="topbar">
  <div class="topbar-inner">
    <div><strong>{escape_html(title)}</strong></div>
    <nav class="navlinks">
      <a href="index.html">Index</a>
      <a href="hikaru_timeline.html">Timeline</a>
      <a href="hikaru_section_signals.html">Section Signals</a>
      <a href="sem_variant_comparison.html">Variant</a>
    </nav>
  </div>
</div>
<main>
{body}
</main>
</body>
</html>
"""
    output.write_text(html, encoding="utf-8")


def escape_html(value: object) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return "" if value is None else str(value)


def table_html(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    header = "".join(f"<th>{escape_html(label)}</th>" for _, label in columns)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{escape_html(fmt(row.get(key)))}</td>" for key, _ in columns)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<div class=\"table-wrap\"><table><thead><tr>{header}</tr></thead><tbody>{''.join(body_rows)}</tbody></table></div>"


def plotly_script(include: bool = True) -> str:
    return '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>' if include else ""


def scatter_by_group(
    div_id: str,
    rows: list[dict[str, Any]],
    x_key: str,
    y_key: str,
    group_key: str,
    title: str,
    hover_keys: list[str],
) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(group_key, "unknown"))].append(row)
    traces = []
    for group, items in grouped.items():
        traces.append(
            {
                "type": "scatter",
                "mode": "markers+lines",
                "name": group,
                "x": [item.get(x_key) for item in items],
                "y": [item.get(y_key) for item in items],
                "text": [_hover_text(item, hover_keys) for item in items],
                "hovertemplate": "%{text}<extra></extra>",
            }
        )
    return _plot(div_id, traces, title, x_key, y_key)


def bar_chart(
    div_id: str,
    rows: list[dict[str, Any]],
    x_key: str,
    y_key: str,
    title: str,
    hover_keys: list[str] | None = None,
) -> str:
    hover_keys = hover_keys or []
    traces = [
        {
            "type": "bar",
            "x": [row.get(x_key) for row in rows],
            "y": [row.get(y_key) for row in rows],
            "text": [_hover_text(row, hover_keys) for row in rows],
            "hovertemplate": "%{text}<extra></extra>",
        }
    ]
    return _plot(div_id, traces, title, x_key, y_key)


def grouped_bar_chart(
    div_id: str,
    rows: list[dict[str, Any]],
    x_key: str,
    a_key: str,
    b_key: str,
    title: str,
) -> str:
    x = [row.get(x_key) for row in rows]
    traces = [
        {"type": "bar", "name": "Variant A", "x": x, "y": [row.get(a_key) for row in rows]},
        {"type": "bar", "name": "Variant B", "x": x, "y": [row.get(b_key) for row in rows]},
    ]
    return _plot(div_id, traces, title, x_key, "value", {"barmode": "group"})


def line_chart(div_id: str, x: list[Any], y: list[Any], title: str, x_title: str, y_title: str) -> str:
    traces = [{"type": "scatter", "mode": "lines", "name": y_title, "x": x, "y": y}]
    return _plot(div_id, traces, title, x_title, y_title)


def _plot(
    div_id: str,
    traces: list[dict[str, Any]],
    title: str,
    x_title: str,
    y_title: str,
    extra_layout: dict[str, Any] | None = None,
) -> str:
    layout = {
        "title": title,
        "xaxis": {"title": x_title},
        "yaxis": {"title": y_title},
        "margin": {"t": 60, "r": 24, "b": 70, "l": 70},
    }
    if extra_layout:
        layout.update(extra_layout)
    return f"""
<div class="chart-card">
<div id="{escape_html(div_id)}" class="plot"></div>
</div>
<script>
Plotly.newPlot({json.dumps(div_id)}, {json.dumps(traces)}, {json.dumps(layout)}, {{responsive: true, displaylogo: false, scrollZoom: true}});
</script>
"""


def _hover_text(row: dict[str, Any], keys: list[str]) -> str:
    return "<br>".join(f"{escape_html(key)}: {escape_html(fmt(row.get(key)))}" for key in keys)

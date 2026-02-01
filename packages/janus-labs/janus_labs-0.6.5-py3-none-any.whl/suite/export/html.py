"""HTML export for SuiteResult."""

from html import escape
from pathlib import Path

from suite.result import SuiteResult


def export_html(result: SuiteResult, output_path: str) -> str:
    """
    Generate self-contained HTML report.

    Requirements:
    - No external dependencies (inline CSS/JS)
    - Viewable offline
    - Shows: headline, breakdown table, governance summary
    - Professional styling (dark theme preferred)

    Returns:
        Path to generated HTML file
    """
    rows = "\n".join(
        (
            "<tr>"
            f"<td>{score.behavior_id}</td>"
            f"<td>{score.name}</td>"
            f"<td>{score.score:.1f}</td>"
            f"<td>{score.grade}</td>"
            f"<td>{'yes' if score.passed else 'no'}</td>"
            f"<td>{'yes' if score.halted else 'no'}</td>"
            "</tr>"
        )
        for score in result.behavior_scores
    )

    halted_behaviors = ", ".join(result.governance_flags.halted_behaviors) or "none"
    config_badge = ""
    if result.config_metadata:
        if result.config_metadata.config_source == "custom":
            files = ", ".join(result.config_metadata.config_files)
            config_badge = (
                '<span class="badge badge-custom" '
                f'title="Custom config: {escape(files, quote=True)}">'
                "&#9881;&#65039; Custom</span>"
            )
        else:
            config_badge = '<span class="badge badge-default">&#128230; Default</span>'

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Janus Labs Suite Report</title>
  <style>
    body {{
      font-family: "Segoe UI", Arial, sans-serif;
      background: #0f1117;
      color: #e6e6e6;
      margin: 0;
      padding: 32px;
    }}
    .card {{
      background: #151922;
      border: 1px solid #2a2f3a;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    }}
    h1, h2 {{
      margin: 0 0 12px 0;
    }}
    .headline {{
      font-size: 48px;
      font-weight: 700;
    }}
    .grade {{
      font-size: 24px;
      font-weight: 600;
      color: #8dd18f;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      border-bottom: 1px solid #2a2f3a;
      padding: 10px 8px;
      text-align: left;
    }}
    th {{
      color: #9aa3b2;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .muted {{
      color: #9aa3b2;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 0.75rem;
      font-weight: 500;
      margin-left: 8px;
    }}
    .badge-custom {{
      background: #0d9488;
      color: white;
    }}
    .badge-default {{
      background: #6b7280;
      color: white;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{result.suite_id} ({result.suite_version}) {config_badge}</h1>
    <div class="headline">{result.headline_score:.1f}</div>
    <div class="grade">Grade {result.grade}</div>
    <div class="muted">Comparability key: {result.comparability_key}</div>
  </div>

  <div class="card">
    <h2>Behavior Breakdown</h2>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Score</th>
          <th>Grade</th>
          <th>Passed</th>
          <th>Halted</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Governance Summary</h2>
    <p>Total rollouts: <strong>{result.total_rollouts}</strong></p>
    <p>Any halted: <strong>{'yes' if result.governance_flags.any_halted else 'no'}</strong></p>
    <p>Halted count: <strong>{result.governance_flags.halted_count}</strong></p>
    <p>Halted behaviors: <strong>{halted_behaviors}</strong></p>
    <p>Foundation check rate: <strong>{result.governance_flags.foundation_check_rate:.2f}</strong></p>
  </div>
</body>
</html>
"""

    output = Path(output_path)
    output.write_text(html, encoding="utf-8")
    return str(output)

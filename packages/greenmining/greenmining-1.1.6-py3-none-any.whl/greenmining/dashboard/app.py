# Flask-based web dashboard for GreenMining analysis visualization.
# Provides interactive charts for repository analysis, pattern distribution,
# temporal trends, and energy consumption.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def create_app(data_dir: str = "./data"):
    # Create Flask application for the dashboard.
    # Args:
    #   data_dir: Path to directory containing analysis JSON files
    # Returns:
    #   Flask application instance
    try:
        from flask import Flask, render_template_string, jsonify, request
    except ImportError:
        raise ImportError("Flask is required for the dashboard. Install it with: pip install flask")

    app = Flask(__name__)
    data_path = Path(data_dir)

    def _load_data(filename: str) -> Dict[str, Any]:
        filepath = data_path / filename
        if filepath.exists():
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        return {}

    @app.route("/")
    def index():
        return render_template_string(DASHBOARD_HTML)

    @app.route("/api/repositories")
    def api_repositories():
        data = _load_data("repositories.json")
        return jsonify(data)

    @app.route("/api/analysis")
    def api_analysis():
        data = _load_data("analysis_results.json")
        return jsonify(data)

    @app.route("/api/statistics")
    def api_statistics():
        data = _load_data("aggregated_statistics.json")
        return jsonify(data)

    @app.route("/api/energy")
    def api_energy():
        data = _load_data("energy_report.json")
        return jsonify(data)

    @app.route("/api/summary")
    def api_summary():
        # Build summary from available data
        repos = _load_data("repositories.json")
        analysis = _load_data("analysis_results.json")

        repo_count = 0
        if isinstance(repos, list):
            repo_count = len(repos)
        elif isinstance(repos, dict):
            repo_count = repos.get("total_repositories", len(repos.get("repositories", [])))

        commit_count = 0
        green_count = 0
        if isinstance(analysis, list):
            commit_count = len(analysis)
            green_count = sum(1 for a in analysis if a.get("green_aware"))
        elif isinstance(analysis, dict):
            results = analysis.get("results", [])
            for r in results:
                commits = r.get("commits", [])
                commit_count += len(commits)
                green_count += sum(1 for c in commits if c.get("green_aware"))

        green_rate = (green_count / commit_count * 100) if commit_count > 0 else 0

        return jsonify(
            {
                "repositories": repo_count,
                "commits_analyzed": commit_count,
                "green_commits": green_count,
                "green_rate": round(green_rate, 1),
            }
        )

    return app


def run_dashboard(data_dir: str = "./data", host: str = "127.0.0.1", port: int = 5000):
    # Run the dashboard server.
    # Args:
    #   data_dir: Path to analysis data directory
    #   host: Host to bind to
    #   port: Port to bind to
    app = create_app(data_dir)
    print(f"GreenMining Dashboard running at http://{host}:{port}")
    print(f"Data directory: {data_dir}")
    app.run(host=host, port=port, debug=False)


# Dashboard HTML template with embedded JS (no external dependencies)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GreenMining Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f5f7fa; color: #333; }
        .header { background: #1a472a; color: white; padding: 20px 40px; }
        .header h1 { font-size: 24px; font-weight: 600; }
        .header p { font-size: 14px; opacity: 0.8; margin-top: 4px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
        .card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .card h3 { font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
        .card .value { font-size: 32px; font-weight: 700; color: #1a472a; margin-top: 8px; }
        .card .subtitle { font-size: 12px; color: #999; margin-top: 4px; }
        .section { margin-bottom: 24px; }
        .section h2 { font-size: 18px; margin-bottom: 12px; color: #1a472a; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px;
                overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-size: 12px; text-transform: uppercase; color: #666; }
        td { font-size: 14px; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; }
        .badge-green { background: #d4edda; color: #155724; }
        .badge-gray { background: #e9ecef; color: #495057; }
        .bar { height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; }
        .bar-fill { height: 100%; background: #1a472a; border-radius: 4px;
                     transition: width 0.5s ease; }
        .loading { text-align: center; padding: 40px; color: #999; }
    </style>
</head>
<body>
    <div class="header">
        <h1>GreenMining Dashboard</h1>
        <p>Mining Software Repositories for Green IT Research</p>
    </div>
    <div class="container">
        <div class="grid" id="summary-cards">
            <div class="card"><h3>Repositories</h3><div class="value" id="repo-count">-</div></div>
            <div class="card"><h3>Commits Analyzed</h3><div class="value" id="commit-count">-</div></div>
            <div class="card"><h3>Green Commits</h3><div class="value" id="green-count">-</div></div>
            <div class="card"><h3>Green Rate</h3><div class="value" id="green-rate">-</div></div>
        </div>
        <div class="section">
            <h2>Repositories</h2>
            <div id="repo-table"><div class="loading">Loading data...</div></div>
        </div>
    </div>
    <script>
        async function loadDashboard() {
            try {
                const summary = await fetch('/api/summary').then(r => r.json());
                document.getElementById('repo-count').textContent = summary.repositories;
                document.getElementById('commit-count').textContent = summary.commits_analyzed.toLocaleString();
                document.getElementById('green-count').textContent = summary.green_commits.toLocaleString();
                document.getElementById('green-rate').textContent = summary.green_rate + '%';
            } catch(e) {
                console.log('Summary not available:', e);
            }

            try {
                const repos = await fetch('/api/repositories').then(r => r.json());
                const list = repos.repositories || (Array.isArray(repos) ? repos : []);
                if (list.length > 0) {
                    let html = '<table><thead><tr><th>Repository</th><th>Language</th>' +
                        '<th>Stars</th><th>Description</th></tr></thead><tbody>';
                    list.slice(0, 50).forEach(r => {
                        html += '<tr><td><strong>' + (r.full_name || r.name) + '</strong></td>' +
                            '<td><span class="badge badge-green">' + (r.language || '-') + '</span></td>' +
                            '<td>' + (r.stars || 0).toLocaleString() + '</td>' +
                            '<td>' + (r.description || '-').substring(0, 80) + '</td></tr>';
                    });
                    html += '</tbody></table>';
                    document.getElementById('repo-table').innerHTML = html;
                } else {
                    document.getElementById('repo-table').innerHTML =
                        '<div class="card">No repository data found. Run an analysis first.</div>';
                }
            } catch(e) {
                document.getElementById('repo-table').innerHTML =
                    '<div class="card">Run an analysis to populate the dashboard.</div>';
            }
        }
        loadDashboard();
    </script>
</body>
</html>
"""

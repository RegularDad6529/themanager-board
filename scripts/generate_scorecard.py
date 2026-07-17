#!/usr/bin/env python3
"""
TheManager Scorecard — Gemba Board Generator

Reads dashboard data from JSON and renders a dark-themed HTML gemba board.
Each wave/activity gets its own zone with headline KPIs.
Zones are configurable — add/remove waves in config/scorecard_config.json.

Output: HTML file + PNG screenshot (via Playwright).
"""
import json, os, sys
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")
OUTPUT_DIR = os.path.join(BASE, "output")
CONFIG_FILE = os.path.join(BASE, "config", "scorecard_config.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE, "config"), exist_ok=True)

# === CONFIG ===
# Defines which zones appear on the board and which data keys to display.
# Add/remove zones here — the generator will pick up changes automatically.
DEFAULT_CONFIG = {
    "title": "TheManager Scorecard",
    "subtitle": "6529 Daily Operations Dashboard",
    "zones": [
        {
            "id": "giphy",
            "label": "GIPHY",
            "color": "#22d3ee",
            "icon": "📊",
            "metrics": [
                {"key": "channel_views", "label": "Total Views", "format": "string"},
                {"key": "channel_uploads", "label": "Uploads", "format": "string"},
                {"key": "local_meme_cards", "label": "Meme Cards", "format": "int"},
                {"key": "failed", "label": "Failed", "format": "int"},
            ]
        },
        {
            "id": "meme_club",
            "label": "MEME CLUB",
            "color": "#34d399",
            "icon": "🗳️",
            "metrics": [
                {"key": "current_winner", "label": "Leader", "format": "handle"},
                {"key": "current_winner_votes", "label": "Votes", "format": "votes"},
                {"key": "current_winner_voters", "label": "Voters", "format": "int"},
                {"key": "active_submissions", "label": "Submissions", "format": "int"},
            ]
        },
        {
            "id": "shill_watch",
            "label": "SHILL WATCH",
            "color": "#fb7185",
            "icon": "🔍",
            "metrics": [
                {"key": "total_shills_caught", "label": "Shills Caught", "format": "int"},
            ]
        },
        {
            "id": "do_something",
            "label": "DO SOMETHING",
            "color": "#fbbf24",
            "icon": "🎯",
            "metrics": [
                {"key": "total_submissions", "label": "Submissions", "format": "int"},
                {"key": "completed", "label": "Completed", "format": "int"},
                {"key": "in_progress", "label": "In Progress", "format": "int"},
                {"key": "ms_won", "label": "MS Wins", "format": "int"},
            ]
        },
        {
            "id": "complaints",
            "label": "COMPLAINTS",
            "color": "#a78bfa",
            "icon": "📞",
            "metrics": [
                {"key": "card_images_posted", "label": "Cards Posted", "format": "int"},
                {"key": "complainers_recruited", "label": "Recruited", "format": "int"},
                {"key": "mentions_handled", "label": "Mentions", "format": "int"},
            ]
        },
        {
            "id": "vetting",
            "label": "VETTING",
            "color": "#fb923c",
            "icon": "👤",
            "metrics": [
                {"key": "total_assessments", "label": "Assessments", "format": "int"},
                {"key": "pitfalls", "label": "Pitfalls", "format": "int"},
                {"key": "weekly_commits", "label": "Commits (7d)", "format": "int"},
            ]
        },
    ]
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    # Write default config
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    return DEFAULT_CONFIG

def load_data():
    """Load the most recent dashboard data."""
    history_file = "/home/prenode/.hermes/profiles/themanager/seen/dashboard_history.json"
    if not os.path.exists(history_file):
        print("ERROR: No dashboard history found. Run dashboard_collector.py first.")
        sys.exit(1)
    
    with open(history_file) as f:
        history = json.load(f)
    
    # Get latest entries for each category
    data = {}
    for category, entries in history.items():
        if entries and isinstance(entries, list):
            # Get the most recent non-error entry
            for entry in reversed(entries):
                if "error" not in entry:
                    data[category] = entry
                    break
    
    return data

def format_value(value, fmt):
    if value is None:
        return "—"
    if fmt == "int":
        return str(int(value))
    if fmt == "votes":
        if isinstance(value, (int, float)):
            if value >= 1_000_000:
                return f"{value/1_000_000:.1f}M"
            elif value >= 1_000:
                return f"{value/1_000:.1f}K"
            return str(int(value))
        return str(value)
    if fmt == "handle":
        return f"@{value}" if value and not str(value).startswith("@") else str(value)
    if fmt == "string":
        return str(value)
    return str(value)

def generate_html(config, data):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    zones = config.get("zones", [])
    
    # Build zone cards HTML
    zone_cards = []
    for zone in zones:
        zone_data = data.get(zone["id"], {})
        color = zone.get("color", "#64748b")
        icon = zone.get("icon", "■")
        label = zone.get("label", zone["id"].upper())
        
        # Wave link (shared across layouts)
        wave_url = zone.get("wave_url", "")
        link_html = ""
        if wave_url:
            link_html = f'<a href="{wave_url}" target="_blank" class="zone-link">↗ wave</a>'
        graph_url = zone.get("graph_url", "")
        if graph_url:
            link_html += f' <a href="{graph_url}" target="_blank" class="zone-link">📈 graph</a>'
        
        # Check for hero layout (winner on top, stats below)
        layout = zone.get("layout", "grid")
        
        if layout == "hero":
            # Hero layout: first metric is large, rest are small below
            hero_metric = zone.get("metrics", [{}])[0]
            hero_val = format_value(zone_data.get(hero_metric["key"]), hero_metric.get("format", "string"))
            sub_metrics = zone.get("metrics", [])[1:]
            
            sub_html = ""
            for m in sub_metrics:
                val = format_value(zone_data.get(m["key"]), m.get("format", "string"))
                sub_html += f'<span class="hero-sub"><span class="hero-sub-value" style="color: {color}">{val}</span> <span class="hero-sub-label">{m["label"]}</span></span>'
            
            zone_cards.append(f"""
        <div class="zone-card hero-card" style="border-color: {color}40;">
          <div class="zone-header" style="border-bottom-color: {color}30;">
            <span class="zone-icon">{icon}</span>
            <span class="zone-label" style="color: {color}">{label}</span>
            {link_html}
          </div>
          <div class="hero-value" style="color: {color}">{hero_val}</div>
          <div class="hero-stats">{sub_html}</div>
        </div>""")
        else:
            # Standard grid layout
            metrics_html = []
            for metric in zone.get("metrics", []):
                key = metric["key"]
                val = zone_data.get(key)
                formatted = format_value(val, metric.get("format", "string"))
                metrics_html.append(f"""
              <div class="metric">
                <div class="metric-value" style="color: {color}">{formatted}</div>
                <div class="metric-label">{metric['label']}</div>
              </div>""")
            
            metrics_str = "".join(metrics_html)
            n_metrics = len(zone.get("metrics", []))
            if n_metrics <= 1:
                grid_cols = "1"
            elif n_metrics <= 2:
                grid_cols = "2"
            elif n_metrics <= 4:
                grid_cols = "2"
            else:
                grid_cols = "3"
            
            zone_cards.append(f"""
        <div class="zone-card" style="border-color: {color}40;">
          <div class="zone-header" style="border-bottom-color: {color}30;">
            <span class="zone-icon">{icon}</span>
            <span class="zone-label" style="color: {color}">{label}</span>
            {link_html}
          </div>
          <div class="zone-metrics" style="grid-template-columns: repeat({grid_cols}, 1fr);">
            {metrics_str}
          </div>
        </div>""")
    
    zones_html = "".join(zone_cards)
    
    # Count zones for grid layout — portrait orientation
    n_zones = len(zones)
    zones_grid = "2"  # 2 columns for portrait layout
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TheManager Scorecard — {today}</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  font-family: 'JetBrains Mono', monospace;
  background: #020617;
  min-height: 100vh;
  padding: 1.25rem;
  color: white;
}}

.scorecard {{
  max-width: 560px;
  margin: 0 auto;
}}

.header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #1e293b;
}}

.header-left {{
  display: flex;
  align-items: center;
  gap: 0.75rem;
}}

.pulse-dot {{
  width: 10px;
  height: 10px;
  background: #22d3ee;
  border-radius: 50%;
  animation: pulse 2s infinite;
}}

@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.4; }}
}}

h1 {{
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.025em;
  text-transform: uppercase;
}}

.header-date {{
  color: #475569;
  font-size: 0.875rem;
  font-weight: 500;
}}

.zones {{
  display: grid;
  grid-template-columns: repeat({zones_grid}, 1fr);
  gap: 0.75rem;
}}

.zone-card {{
  background: rgba(15, 23, 42, 0.6);
  border-radius: 0.75rem;
  border: 1px solid;
  padding: 0.75rem;
}}

.zone-header {{
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.5rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid;
}}

.zone-icon {{
  font-size: 1.1rem;
}}

.zone-label {{
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  flex: 1;
}}

.zone-link {{
  color: #475569;
  text-decoration: none;
  font-size: 0.8rem;
  transition: color 0.2s;
}}

.zone-link:hover {{
  color: #94a3b8;
}}

.zone-metrics {{
  display: grid;
  gap: 0.5rem;
}}

/* Hero layout for MC winner */
.hero-card {{
  display: flex;
  flex-direction: column;
}}

.hero-value {{
  font-size: 1.5rem;
  font-weight: 800;
  text-align: center;
  padding: 0.25rem 0.5rem 0.5rem;
  letter-spacing: -0.02em;
}}

.hero-stats {{
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  padding: 0 0.5rem 0.25rem;
}}

.hero-sub {{
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}}

.hero-sub-value {{
  font-size: 1.1rem;
  font-weight: 700;
}}

.hero-sub-label {{
  font-size: 0.625rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}

.metric {{
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}}

.metric-value {{
  font-size: 1.5rem;
  font-weight: 800;
  line-height: 1.2;
}}

.metric-label {{
  font-size: 0.65rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}

.footer {{
  text-align: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #1e293b;
  color: #475569;
  font-size: 0.7rem;
}}

.footer a {{
  color: #475569;
  text-decoration: none;
}}
</style>
</head>
<body>
<div class="scorecard">
  <div class="header">
    <div class="header-left">
      <div class="pulse-dot"></div>
      <h1>{config.get('title', 'TheManager Scorecard')}</h1>
    </div>
    <div class="header-date">{today}</div>
  </div>
  
  <div class="zones">
{zones_html}
  </div>
  
  <div class="footer">
    TheManager Scorecard · 6529 Daily Operations · <a href="https://github.com/RegularDad6529/themanager-scorecard">github.com/RegularDad6529/themanager-scorecard</a>
  </div>
</div>
</body>
</html>"""
    
    return html

def screenshot_html(html_path, png_path, width=800, height=1000):
    """Use Playwright to screenshot the HTML to a PNG, cropped to content."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(500)  # Wait for fonts to load
        # Screenshot only the scorecard div, not the full page
        elt = page.query_selector(".scorecard")
        if elt:
            elt.screenshot(path=png_path)
        else:
            page.screenshot(path=png_path, full_page=True)
        browser.close()

def generate_views_graph(history):
    """Generate a standalone HTML page with daily/weekly Giphy view trends."""
    giphy_history = history.get("giphy", [])
    
    # Parse view counts to numeric values
    data_points = []
    for entry in giphy_history:
        if "error" in entry:
            continue
        views_str = entry.get("channel_views", "0")
        # Parse "117.4K" or "1.2M" format
        try:
            if "K" in views_str:
                views = float(views_str.replace("K", "")) * 1000
            elif "M" in views_str:
                views = float(views_str.replace("M", "")) * 1_000_000
            else:
                views = float(views_str)
            data_points.append({
                "date": entry.get("date", ""),
                "views": views,
                "raw": views_str,
            })
        except (ValueError, TypeError):
            continue
    
    if not data_points:
        return "<html><body><p>No view data yet.</p></body></html>"
    
    # Build SVG line chart
    max_views = max(d["views"] for d in data_points)
    min_views = min(d["views"] for d in data_points) if data_points else 0
    range_views = max(max_views - min_views, 1)
    
    chart_w = 800
    chart_h = 300
    padding = 40
    plot_w = chart_w - padding * 2
    plot_h = chart_h - padding * 2
    
    n = len(data_points)
    points = []
    for i, d in enumerate(data_points):
        x = padding + (plot_w * i / max(n - 1, 1))
        y = padding + plot_h - (plot_h * (d["views"] - min_views) / range_views)
        points.append((x, y, d))
    
    # Build polyline
    polyline = " ".join(f"{x},{y}" for x, y, _ in points)
    
    # Build data point circles and labels
    circles = ""
    labels = ""
    for x, y, d in points:
        circles += f'<circle cx="{x}" cy="{y}" r="4" fill="#22d3ee" />'
        if n <= 14:  # Only show labels if not too many points
            labels += f'<text x="{x}" y="{y - 12}" fill="#94a3b8" font-size="9" text-anchor="middle">{d["raw"]}</text>'
            labels += f'<text x="{x}" y="{chart_h - 15}" fill="#64748b" font-size="8" text-anchor="middle">{d["date"][5:]}</text>'
    
    # Calculate weekly delta if we have enough data
    weekly_delta = ""
    if len(data_points) >= 7:
        recent = data_points[-1]["views"]
        week_ago = data_points[-7]["views"]
        delta = recent - week_ago
        pct = (delta / week_ago * 100) if week_ago > 0 else 0
        weekly_delta = f'<div class="stat">Weekly: <span style="color: {"#34d399" if delta >= 0 else "#fb7185"}">{"+" if delta >= 0 else ""}{delta:,.0f} ({pct:+.1f}%)</span></div>'
    
    daily_delta = ""
    if len(data_points) >= 2:
        recent = data_points[-1]["views"]
        prev = data_points[-2]["views"]
        delta = recent - prev
        daily_delta = f'<div class="stat">Daily: <span style="color: {"#34d399" if delta >= 0 else "#fb7185"}">{"+" if delta >= 0 else ""}{delta:,.0f}</span></div>'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Giphy Views — TheManager Scorecard</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'JetBrains Mono', monospace; background: #020617; color: white; padding: 2rem; }}
.container {{ max-width: 900px; margin: 0 auto; }}
h1 {{ font-size: 1.25rem; font-weight: 800; margin-bottom: 0.5rem; }}
.stats {{ display: flex; gap: 2rem; margin-bottom: 1.5rem; }}
.stat {{ font-size: 0.875rem; color: #94a3b8; }}
.stat span {{ font-weight: 700; }}
.chart-container {{ background: rgba(15, 23, 42, 0.6); border-radius: 0.75rem; border: 1px solid #1e293b; padding: 1.5rem; }}
.back {{ color: #475569; text-decoration: none; font-size: 0.75rem; }}
.back:hover {{ color: #94a3b8; }}
</style>
</head>
<body>
<div class="container">
  <a href="index.html" class="back">← Back to Scorecard</a>
  <h1 style="margin-top: 1rem;">📊 Giphy Views Trend</h1>
  <div class="stats">
    <div class="stat">Current: <span style="color: #22d3ee">{data_points[-1]["raw"]}</span></div>
    {daily_delta}
    {weekly_delta}
  </div>
  <div class="chart-container">
    <svg viewBox="0 0 {chart_w} {chart_h}" style="width: 100%;">
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />
      <polyline points="{polyline}" fill="none" stroke="#22d3ee" stroke-width="2" />
      {circles}
      {labels}
    </svg>
  </div>
  <p style="color: #475569; font-size: 0.7rem; margin-top: 1rem;">Data collected daily from giphy.com/channel/RegularDad</p>
</div>
</body>
</html>"""
    
    return html

def main():
    config = load_config()
    data = load_data()
    
    if not data:
        print("ERROR: No data available")
        sys.exit(1)
    
    # Generate HTML
    html = generate_html(config, data)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    html_path = os.path.join(OUTPUT_DIR, f"scorecard_{today}.html")
    png_path = os.path.join(OUTPUT_DIR, f"scorecard_{today}.png")
    
    with open(html_path, "w") as f:
        f.write(html)
    print(f"HTML saved: {html_path}")
    
    # Also save a copy as index.html for git display
    index_path = os.path.join(BASE, "index.html")
    with open(index_path, "w") as f:
        f.write(html)
    print(f"Index saved: {index_path}")
    
    # Save data snapshot
    data_path = os.path.join(DATA_DIR, f"data_{today}.json")
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Data saved: {data_path}")
    
    # Generate views graph page
    history_file = "/home/prenode/.hermes/profiles/themanager/seen/dashboard_history.json"
    if os.path.exists(history_file):
        with open(history_file) as f:
            history = json.load(f)
        views_html = generate_views_graph(history)
        views_path = os.path.join(BASE, "views.html")
        with open(views_path, "w") as f:
            f.write(views_html)
        print(f"Views graph saved: {views_path}")
    
    # Screenshot
    try:
        screenshot_html(os.path.abspath(html_path), os.path.abspath(png_path))
        print(f"PNG saved: {png_path}")
    except Exception as e:
        print(f"Screenshot failed: {e}")
        print("HTML is still available for manual screenshot")

if __name__ == "__main__":
    main()
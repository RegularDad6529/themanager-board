# TheManager Scorecard

Daily gemba board for 6529 operations — auto-generated from live data.

## Structure

```
config/scorecard_config.json   — Zone definitions (add/remove waves here)
scripts/generate_scorecard.py  — Renders HTML + PNG from dashboard data
scripts/update_and_commit.sh   — Collect data, generate, commit, push
data/                          — Daily JSON snapshots
output/                        — Daily HTML + PNG scorecards
index.html                     — Latest scorecard (for GitHub Pages)
```

## Zones

Each zone represents a wave or activity. Add/remove in `config/scorecard_config.json`:

| Zone | Color | Data Source |
|------|-------|-------------|
| 📊 Giphy | Cyan | Giphy channel scrape + local state |
| 🗳️ Meme Club | Emerald | 6529 leaderboard API |
| 🔍 Shill Watch | Rose | Shill watcher log |
| 🎯 Do Something | Amber | Do Something tracking JSON |
| 📞 Complaints | Violet | Card pipeline logs + seen files |
| 👤 Vetting | Orange | Git repo + pitfalls.md |

## Daily Update

Run manually or via cron:
```bash
# 1. Collect dashboard data
python3 /home/user/.hermes/profiles/themanager/scripts/dashboard_collector.py

# 2. Generate scorecard
python3 /home/user/themanager-scorecard/scripts/generate_scorecard.py

# 3. Commit and push
cd /home/user/themanager-scorecard
git add -A && git commit -m "Scorecard $(date -u +%Y-%m-%d)" && git push
```

## License

CC0 — same as 6529 ecosystem.
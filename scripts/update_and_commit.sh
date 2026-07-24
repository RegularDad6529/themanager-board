#!/bin/bash
# Daily update script — collect data, generate scorecard, commit, push
set -e

echo "=== TheManager Scorecard Daily Update ==="

# 1. Collect dashboard data
echo "Collecting dashboard data..."
python3 /home/user/.hermes/profiles/themanager/scripts/dashboard_collector.py

# 2. Generate scorecard
echo "Generating scorecard..."
python3 /home/user/themanager-scorecard/scripts/generate_scorecard.py

# 3. Commit and push
echo "Committing to git..."
cd /home/user/themanager-scorecard
git add -A
TODAY=$(date -u +%Y-%m-%d)
git commit -m "Scorecard $TODAY" || echo "Nothing to commit"
git push origin main || echo "Push failed — check remote"

echo "=== Done ==="
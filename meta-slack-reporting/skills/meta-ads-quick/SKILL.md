---
name: meta-ads-quick
description: "Fast daily Meta Ads performance snapshot with top campaigns and metrics"
---

# Meta Ads Quick Report

Get a fast daily performance snapshot of your Meta Ads campaigns.

## What This Does

Provides a rapid overview of your Meta advertising performance without the overhead of AI analysis or historical tracking. Perfect for quick daily check-ins.

## Usage

```bash
/meta-ads-quick [--account gre|upsc] [--days 7]
```

## Arguments

- `--account` (optional): Account to report on
  - `gre` (default): PrepAiro GRE account
  - `upsc`: UPSC account
- `--days` (optional): Number of days to include in report (default: 7)

## What You Get

1. **Summary Metrics**: Total spend, impressions, reach, clicks, and CTR
2. **Top 5 Campaigns**: Ranked by spend with performance breakdown
3. **Daily Breakdown**: Spend and engagement for each day
4. **Status Indicators**: Visual status for each campaign (🟢 Active, 🟡 Paused, etc.)

## Output

Report is delivered directly to your configured Slack channel.

## Performance

Completes in ~30 seconds - faster than the full intelligent analysis.

## When to Use This Skill

✅ **Use /meta-ads-quick when:**
- You need a quick morning check-in
- You want to see yesterday's or last week's performance
- You need a fast overview without deep analysis
- You're in a hurry and don't need AI insights
- You want to check top campaigns by spend
- You need daily metrics for a standup meeting

❌ **Don't use this when:**
- You need conversion metrics (CPI, CPR, CPA) → Use /meta-ads-analyze
- You want AI-powered insights → Use /meta-ads-analyze
- You need historical trends → Use /meta-ads-analyze
- You want to check platform configuration → Use /meta-ads-audit
- You need visual charts → Use /meta-ads-analyze

## Examples

```bash
# Quick check on GRE account
/meta-ads-quick

# UPSC account for last 30 days
/meta-ads-quick --account upsc --days 30

# Today's performance only
/meta-ads-quick --days 1
```

## Requirements

- Meta Ads account configured in `.env` file
- Valid Meta access token
- Slack webhook URL configured

## Tool Implementation

This skill executes: `tools/quick_report.py`

The tool:
1. Loads configuration from account-specific `.env` file
2. Connects to Meta Ads API
3. Fetches campaign insights and metrics
4. Aggregates data by campaign and day
5. Formats as Slack-compatible message
6. Sends to configured webhook
7. Returns success/failure status

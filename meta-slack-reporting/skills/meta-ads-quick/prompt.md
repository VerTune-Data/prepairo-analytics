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

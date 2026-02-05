---
name: meta-ads-quick
description: "Fetch Meta Ads performance data for conversational analysis with product managers and marketers"
---

# Meta Ads Quick Data Fetcher

Fetches current Meta Ads campaign performance data and returns it to Claude for conversational presentation.

## Purpose

This skill enables Claude to answer questions about Meta Ads performance by fetching real-time data from the Meta Ads API. The data is returned to Claude, who then presents it conversationally based on the user's questions.

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

Returns structured JSON data to Claude containing:
- Campaign performance metrics
- Top campaigns by spend
- Daily breakdown
- Status information

Claude then presents this information conversationally to the user.

## Performance

Completes in ~30 seconds - faster than the full intelligent analysis.

## When Claude Should Use This

✅ **Use when user asks:**
- "How are my ads performing?"
- "What's my ad spend today/this week?"
- "Which campaigns are spending the most?"
- "Show me yesterday's performance"
- "Quick overview of my Meta Ads"
- "What's the status of my campaigns?"

❌ **Don't use when user asks:**
- "Deep analysis with insights" → Use /meta-ads-analyze
- "Which platforms am I running on?" → Use /meta-ads-audit
- "Show me conversion metrics" → Use /meta-ads-analyze
- "Give me AI recommendations" → Use /meta-ads-analyze

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
- Python 3.8+

## Tool Implementation

This skill executes: `tools/quick_report.py`

The tool:
1. Loads configuration from account-specific `.env` file
2. Connects to Meta Ads API
3. Fetches campaign insights and metrics
4. Aggregates data by campaign and day
5. Outputs structured JSON to stdout
6. Claude reads the output and presents conversationally

## Example Conversation

```
User: "How are my GRE ads doing today?"

Claude: [Executes /meta-ads-quick --account gre --days 1]
        [Receives data about spend, impressions, campaigns]

Claude: "Your GRE ads are performing well today! Here's what I see:

        💰 Total spend so far: ₹5,234
        👁️ Impressions: 245K
        👆 Clicks: 3,421 (1.4% CTR)

        Top spending campaigns:
        1. GRE Core Conversions - ₹3,100 (active)
        2. GRE Retargeting - ₹1,890 (active)

        Would you like me to analyze any specific campaign in detail?"
```

---
name: meta-ads-analyze
description: "Deep analysis of Meta Ads with conversions, trends, and AI insights for interactive Q&A"
---

# Meta Ads Deep Analysis

Fetches comprehensive Meta Ads data with conversion tracking and historical trends. Returns structured data to Claude for conversational presentation to product managers and performance marketers.

## What This Does

Provides comprehensive analysis using Claude AI to identify insights, trends, and actionable recommendations. Includes conversion tracking (installs, registrations, purchases), historical comparison, and visual charts.

## Usage

```bash
/meta-ads-analyze [--account gre|upsc] [--range yesterday|7d|30d] [--ai on|off] [--charts on|off]
```

## Arguments

- `--account` (optional): Account to report on
  - `gre` (default): PrepAiro GRE account
  - `upsc`: UPSC account
- `--range` (optional): Time range for analysis (default: yesterday)
  - `yesterday`: Yesterday's complete data (full day)
  - `7d`: Last 7 days
  - `30d`: Last 30 days
- `--ai` (optional): Enable/disable Claude AI analysis (default: on)
- `--charts` (optional): Enable/disable chart generation (default: on)

## What You Get

1. **AI-Powered Insights**: Claude analyzes your data to identify:
   - Critical alerts (money-bleeding campaigns)
   - Conversion winners (best CPI/CPR/CPA)
   - Immediate actions (pause/scale/optimize recommendations)

2. **Historical Trends**: Compare current performance to previous period:
   - Spend changes
   - Conversion efficiency improvements
   - Campaign momentum shifts

3. **Conversion Tracking**: Detailed breakdown of:
   - App installs (CPI)
   - Registrations (CPR)
   - Purchases (CPA)

4. **Visual Charts**: Dual charts showing:
   - Traffic metrics (impressions, clicks, spend)
   - Conversion metrics (installs, registrations, purchases)

5. **Campaign Hierarchy**: Full breakdown:
   - Campaigns → AdSets → Ads
   - Spend, conversions, and efficiency at all levels

## Output

Returns comprehensive JSON data to Claude containing:
- Conversion metrics (installs, registrations, purchases, CPI, CPR, CPA)
- Historical trend comparison (vs previous period)
- Campaign hierarchy (campaigns → adsets → ads)
- Performance deltas and changes
- AI insights and recommendations (optional)

Claude then presents this information conversationally based on user questions.

## Performance

Completes in ~2-3 minutes depending on data volume and AI analysis.

## When Claude Should Use This

✅ **Use when user asks:**
- "What are my conversion metrics?"
- "Show me CPI/CPR/CPA"
- "How do conversions compare to last week?"
- "Give me detailed campaign analysis"
- "Which campaigns are converting best?"
- "What should I optimize?"
- "Deep dive into performance"
- "Show me app install costs"

❌ **Don't use when user asks:**
- "Quick overview" → Use /meta-ads-quick (faster)
- "Platform configuration" → Use /meta-ads-audit
- "Just today's spend" → Use /meta-ads-quick

⚠️ **Note:** First run has no historical comparison. Run it at least twice to get trend analysis.

## Examples

```bash
# Deep analysis of yesterday's performance
/meta-ads-analyze

# UPSC account with full analysis
/meta-ads-analyze --account upsc

# Quick analysis without AI (faster)
/meta-ads-analyze --ai off

# Last 7 days without charts
/meta-ads-analyze --range 7d --charts off
```

## Requirements

- Meta Ads account configured in `.env` file
- Valid Meta access token
- SQLite database for historical tracking
- Python 3.8+
- Optional: Claude API key (for AI insights)

## Notes

- First run: No historical comparison available, only current analysis
- AI analysis requires Claude API key (gracefully skips if unavailable)
- Charts require AWS S3 access (gracefully skips if unavailable)
- Database automatically stores snapshots for future trend analysis

## Tool Implementation

This skill executes: `tools/analyze_report.py`

The tool:
1. Loads configuration from account-specific `.env` file
2. Initializes database for historical tracking
3. Connects to Meta Ads API
4. Fetches comprehensive data (campaigns, adsets, ads, balance)
5. Saves snapshot to database
6. Retrieves previous snapshot for comparison
7. Calculates deltas and trends
8. Generates Claude AI analysis (if enabled)
9. Creates dual charts (traffic + conversions)
10. Uploads charts to S3
11. Formats multi-message Slack report
12. Sends to configured webhook
13. Cleans up old database entries

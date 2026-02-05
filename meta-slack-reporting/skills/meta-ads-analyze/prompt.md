# Meta Ads Analyze

Deep AI-powered analysis of your Meta Ads campaigns with historical trends and conversion tracking.

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

Multi-message report delivered to your configured Slack channel with:
- AI analysis
- Traffic chart (hosted on S3)
- Conversion chart (hosted on S3)
- Detailed campaign breakdown
- Converted users details

## Performance

Completes in ~2-3 minutes depending on data volume and AI analysis.

## When to Use This Skill

✅ **Use /meta-ads-analyze when:**
- You need deep AI-powered insights and recommendations
- You want to see conversion metrics (installs, registrations, purchases)
- You need historical trend analysis vs previous period
- You're preparing for a team meeting or presentation
- You want visual charts to share
- You need to optimize campaign performance
- You want to identify money-bleeding campaigns
- You're doing weekly or monthly performance reviews

❌ **Don't use this when:**
- You just need a quick overview → Use /meta-ads-quick (faster)
- You want to check platform configuration → Use /meta-ads-audit
- You're in a hurry (this takes 2-3 minutes)

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
- Slack webhook URL configured
- Claude API key in AWS Secrets Manager or environment variable (for AI analysis)
- AWS credentials configured (for S3 chart hosting)
- SQLite database for historical tracking

## Notes

- First run: No historical comparison available, only current analysis
- AI analysis requires Claude API key (gracefully skips if unavailable)
- Charts require AWS S3 access (gracefully skips if unavailable)
- Database automatically stores snapshots for future trend analysis

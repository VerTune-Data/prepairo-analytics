# Meta Ads Management Skills

Three focused skills to help product teams manage Meta Ads campaigns without technical knowledge.

## Quick Reference

| Skill | Purpose | Speed | Output |
|-------|---------|-------|--------|
| `/meta-ads-quick` | Fast daily snapshot | ~30s | Slack report |
| `/meta-ads-analyze` | Deep AI analysis | ~2-3min | Slack with charts |
| `/meta-ads-audit` | Platform checker | ~10s | Terminal report |

## Skills Overview

### 1. `/meta-ads-quick` - Fast Daily Snapshot

Get a rapid overview of campaign performance without AI or database overhead.

**Use when:**
- You need a quick daily check-in
- You don't need AI insights or historical trends
- Speed is more important than depth

**What you get:**
- Summary metrics (spend, impressions, reach, clicks, CTR)
- Top 5 campaigns by spend
- Daily breakdown for last 7 days
- Status indicators for each campaign

**Examples:**
```bash
# Quick check on GRE account
/meta-ads-quick

# UPSC account for last 30 days
/meta-ads-quick --account upsc --days 30

# Today's performance only
/meta-ads-quick --days 1
```

---

### 2. `/meta-ads-analyze` - Deep AI-Powered Analysis

Comprehensive analysis with Claude AI, historical trends, and conversion tracking.

**Use when:**
- You need actionable AI-powered insights
- You want to see conversion metrics (CPI, CPR, CPA)
- You need historical trend analysis
- You want visual charts of performance

**What you get:**
- AI insights identifying critical issues and opportunities
- Conversion tracking (app installs, registrations, purchases)
- Historical comparison vs previous period
- Dual charts (traffic metrics + conversion metrics)
- Campaign hierarchy breakdown (campaigns → adsets → ads)

**Examples:**
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

**Note:** First run has no historical comparison. Subsequent runs show trend analysis.

---

### 3. `/meta-ads-audit` - Platform Configuration Checker

Inspect which platforms (Facebook vs Instagram) your campaigns target.

**Use when:**
- You want to verify Instagram-only configuration
- Facebook ads appear despite turning them off
- You need to audit platform spend allocation
- You want to understand campaign targeting

**What you get:**
- Full campaign hierarchy with platform configuration
- Warnings for active adsets with Facebook enabled
- Status of all campaigns and adsets
- Actionable recommendations to fix misconfigurations

**Examples:**
```bash
# Audit GRE account
/meta-ads-audit

# Audit UPSC account
/meta-ads-audit --account upsc
```

**Interpretation:**
- `Publisher Platforms: instagram` = Instagram-only ✅
- `Publisher Platforms: Automatic Placements` = All platforms (FB + IG + more) ⚠️
- 🔴 **FACEBOOK IS ENABLED AND ACTIVE** = Immediate action needed

---

## Installation

All skills are ready to use. No installation required.

**Requirements:**
- Python 3.8+
- Virtual environment with dependencies installed
- Configured `.env` files for each account

---

## Configuration

Each account has its own environment file:
- `.env` - GRE account (default)
- `.env.upsc` - UPSC account
- `.env.test` - Test account

**Required fields:**
```bash
META_ADS_ACCOUNT_ID=act_xxxxx
META_ACCESS_TOKEN=EAxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
ACCOUNT_NAME=PrepAiro GRE
PLATFORMS=instagram  # Optional: instagram-only filtering
```

**Optional fields:**
```bash
REPORT_DAYS=7
TZ=Asia/Kolkata
CLAUDE_API_KEY=sk-xxx  # For AI analysis
AWS_REGION=ap-south-1  # For S3 charts
S3_BUCKET=prepairo-analytics-reports
DB_PATH=meta_ads_history.db
CHARTS_DIR=charts
```

---

## Running Skills

### Command Line (for testing)

```bash
# Activate virtual environment
source venv/bin/activate

# Run quick report
python3 skills/meta-ads-quick/tools/quick_report.py --account gre --days 7

# Run deep analysis
python3 skills/meta-ads-analyze/tools/analyze_report.py --account upsc --ai on

# Run platform audit
python3 skills/meta-ads-audit/tools/audit_platforms.py --account gre
```

### As Skills (recommended)

```bash
# Quick report
/meta-ads-quick --account gre --days 7

# Deep analysis
/meta-ads-analyze --account upsc --ai on --charts on

# Platform audit
/meta-ads-audit --account gre
```

---

## Comparison Table

| Feature | Quick | Analyze | Audit |
|---------|-------|---------|-------|
| **Speed** | ~30s | ~2-3min | ~10s |
| **AI Analysis** | ❌ | ✅ | ❌ |
| **Historical Trends** | ❌ | ✅ | ❌ |
| **Conversion Tracking** | ❌ | ✅ | ❌ |
| **Charts** | ❌ | ✅ | ❌ |
| **Platform Details** | ❌ | ❌ | ✅ |
| **Output** | Slack | Slack | Terminal |
| **Database** | ❌ | ✅ | ❌ |
| **Use Case** | Daily check-in | Deep insights | Config audit |

---

## Troubleshooting

### "Configuration file not found"
- Ensure `.env` (for gre) or `.env.{account}` exists
- Check file is in the project root directory

### "Access token expired"
- Regenerate Meta access token in Facebook Developers
- Update `META_ACCESS_TOKEN` in `.env` file

### "API rate limit exceeded"
- Wait 5-10 minutes before retrying
- Reduce frequency of skill runs

### "Claude API key not found"
- Add `CLAUDE_API_KEY` to environment variable
- Or store in AWS Secrets Manager (name: `meta-ads/claude-api-key`)
- Or disable AI: `/meta-ads-analyze --ai off`

### "S3 upload failed"
- Check AWS credentials are configured (`aws configure`)
- Verify IAM permissions for S3 bucket
- Or disable charts: `/meta-ads-analyze --charts off`

### "No insights data available"
- Verify campaigns have run in the specified date range
- Check if `PLATFORMS=instagram` is filtering out all data
- Ensure Meta access token has `ads_read` permission

---

## Architecture

```
skills/
├── meta-ads-quick/
│   ├── prompt.md               # Skill documentation
│   └── tools/
│       └── quick_report.py     # Fast snapshot script
├── meta-ads-analyze/
│   ├── prompt.md               # Skill documentation
│   └── tools/
│       └── analyze_report.py   # Deep analysis script
└── meta-ads-audit/
    ├── prompt.md               # Skill documentation
    └── tools/
        └── audit_platforms.py  # Platform checker script

modules/
├── config_loader.py            # Multi-account config
├── error_handler.py            # User-friendly errors
├── meta_api.py                 # Meta API wrapper
├── database.py                 # Historical tracking
├── claude_analyzer.py          # AI insights
├── chart_generator.py          # Visualization
├── slack_formatter.py          # Message formatting
├── delta_calculator.py         # Trend analysis
├── s3_uploader.py              # Chart hosting
└── aws_secrets.py              # Secret management
```

---

## Code Reuse

All three skills reuse existing modules:

**meta-ads-quick** reuses:
- `modules/meta_api.py` - API calls
- `modules/config_loader.py` - Config management
- `modules/error_handler.py` - Error handling

**meta-ads-analyze** reuses:
- All modules from `meta_ads_intelligent.py`
- Complete pipeline: API → DB → AI → Charts → Slack

**meta-ads-audit** reuses:
- Logic from `check_platforms.py`
- `modules/config_loader.py` - Config management
- `modules/error_handler.py` - Error handling

**No code duplication** - thin wrappers around existing functionality.

---

## Logs

All skills log to `logs/` directory:
- `logs/meta_ads_quick_YYYYMMDD.log`
- `logs/meta_ads_analyze_YYYYMMDD.log`
- `logs/meta_ads_audit_YYYYMMDD.log`

Check logs for detailed execution information and debugging.

---

## Future Enhancements

Potential improvements:
- Interactive follow-up questions
- Budget alerts and warnings
- A/B testing analysis
- Audience insights
- Automated recommendations
- Scheduling and notifications
- Cost projection
- ROI calculator

---

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Verify `.env` configuration
3. Test with `--help` flag
4. Review error messages (designed to be user-friendly)

---

## Quick Start Guide

**For product teams (non-technical):**

1. **Daily check-in**: `/meta-ads-quick`
   - Fast overview of yesterday's performance
   - No setup required beyond initial config

2. **Weekly deep-dive**: `/meta-ads-analyze`
   - AI-powered insights and trends
   - Visual charts for presentations
   - Conversion metrics for optimization

3. **Configuration check**: `/meta-ads-audit`
   - Verify Instagram-only settings
   - Troubleshoot unexpected Facebook ads
   - Audit platform targeting

**For technical teams:**

1. Review configuration in `.env` files
2. Test each skill with `--help` flag
3. Run with different arguments to explore features
4. Check logs for debugging
5. Customize arguments based on needs

---

## Version History

- **v1.0** (2026-02-05): Initial implementation
  - Three core skills created
  - Shared utility modules
  - Multi-account support
  - Comprehensive error handling

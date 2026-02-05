# Meta Ads Reports - For Product Team

**Simple scripts to get Meta Ads performance reports without any technical knowledge.**

## What You Can Do

Get three types of reports:
1. **Quick Report** - Fast daily snapshot (30 seconds)
2. **Deep Analysis** - AI-powered insights with charts (2-3 minutes)
3. **Platform Audit** - Check Facebook vs Instagram configuration (10 seconds)

All reports are sent directly to your Slack channel automatically.

---

## How to Run Reports

### 1. Quick Daily Report

```bash
./quick-report.sh
```

**What it asks:**
- Which account? (GRE or UPSC)
- How many days? (default: 7)

**What you get:**
- Top 5 campaigns by spend
- Daily breakdown
- Summary metrics (spend, clicks, impressions)
- Delivered to Slack

---

### 2. Deep Analysis with AI

```bash
./analyze-report.sh
```

**What it asks:**
- Which account? (GRE or UPSC)
- Options: Full analysis / Without AI / Without charts / Quick

**What you get:**
- AI recommendations on what to optimize
- Conversion metrics (CPI, CPR, CPA)
- Visual charts
- Historical trends
- Delivered to Slack with charts

---

### 3. Platform Configuration Audit

```bash
./audit-platforms.sh
```

**What it asks:**
- Which account? (GRE or UPSC)

**What you get:**
- Which campaigns run on Facebook vs Instagram
- Warnings if Facebook is enabled when it shouldn't be
- Shows on screen (not sent to Slack)

---

## Examples

### Morning Check-in
```bash
./quick-report.sh
# Select: 1 (GRE)
# Enter: 1 (for yesterday only)
```

### Weekly Team Meeting
```bash
./analyze-report.sh
# Select: 1 (GRE)
# Select: 1 (Full analysis)
```

### Check Platform Settings
```bash
./audit-platforms.sh
# Select: 1 (GRE)
```

---

## Troubleshooting

### "Permission denied"
Run this once:
```bash
chmod +x *.sh
```

### "venv not found"
The Python environment isn't set up. Ask your tech team to run:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "No data available"
- Check if campaigns are running
- Try a longer time period (e.g., 7 or 30 days)

### Report not in Slack
- Check your Slack channel
- Verify webhook URL is correct in `.env` file

---

## What Each Report Shows

### Quick Report
- 💰 Total spend
- 👁️ Impressions (how many times ads shown)
- 👆 Clicks
- 📊 Top performing campaigns
- 📅 Daily breakdown

### Deep Analysis
- 🤖 AI insights (what to pause, what to scale)
- 📈 Trends (compared to previous period)
- 💯 Conversion metrics:
  - CPI = Cost per app install
  - CPR = Cost per registration
  - CPA = Cost per purchase
- 📊 Visual charts (traffic + conversions)

### Platform Audit
- ✅ Instagram-only campaigns
- ⚠️ Campaigns with Facebook enabled
- 🔴 Active campaigns on Facebook (action needed)

---

## When to Use Which Report

| Situation | Use This |
|-----------|----------|
| Daily morning check | `quick-report.sh` (1 day) |
| Weekly review | `analyze-report.sh` |
| Before presentations | `analyze-report.sh` (full) |
| Facebook ads appearing | `audit-platforms.sh` |
| Budget check | `quick-report.sh` (7 days) |
| Performance issues | `analyze-report.sh` (with AI) |

---

## Tips

1. **Save time:** Just press Enter to use defaults
2. **Morning routine:** Run quick-report.sh every day
3. **Weekly meetings:** Run analyze-report.sh on Mondays
4. **Multiple accounts:** You can run reports for both GRE and UPSC
5. **Check Slack:** All reports go to your configured Slack channel

---

## Need Help?

1. Check the Slack channel for the report
2. Run the audit to verify configuration
3. Ask your tech team to check logs in `logs/` folder
4. Read the detailed guide: `skills/README.md`

---

## Advanced: Direct Commands

If you're comfortable with command line, you can also run directly:

```bash
# Quick report
source venv/bin/activate
python3 skills/meta-ads-quick/tools/quick_report.py --account gre --days 7

# Deep analysis
python3 skills/meta-ads-analyze/tools/analyze_report.py --account upsc --ai on

# Platform audit
python3 skills/meta-ads-audit/tools/audit_platforms.py --account gre
```

But the `.sh` wrapper scripts are simpler for most users.

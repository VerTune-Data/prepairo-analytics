# Quick Start Guide: Meta Ads Management Skills

**For product teams who want to run Meta Ads reports without technical knowledge.**

## The Three Skills

### 🚀 Fast Daily Check-in
```bash
/meta-ads-quick
```
**What:** Top campaigns, daily breakdown, summary metrics
**Time:** ~30 seconds
**Output:** Slack message

---

### 🧠 Deep Weekly Analysis
```bash
/meta-ads-analyze
```
**What:** AI insights, trends, conversions, charts
**Time:** ~2-3 minutes
**Output:** Slack message with charts

---

### 🔍 Platform Configuration Check
```bash
/meta-ads-audit
```
**What:** Verify Instagram-only targeting
**Time:** ~10 seconds
**Output:** Terminal report

---

## Common Commands

### Daily Usage
```bash
# Quick morning check
/meta-ads-quick

# Weekly deep-dive
/meta-ads-analyze
```

### Different Accounts
```bash
# GRE account (default)
/meta-ads-quick

# UPSC account
/meta-ads-quick --account upsc
```

### Customization
```bash
# Last 30 days instead of 7
/meta-ads-quick --days 30

# Without AI analysis (faster)
/meta-ads-analyze --ai off

# Without charts (faster)
/meta-ads-analyze --charts off
```

---

## Troubleshooting

### "Configuration file not found"
**Problem:** Missing `.env` file
**Fix:** Ensure `.env` (for GRE) or `.env.upsc` (for UPSC) exists in project root

### "Access token expired"
**Problem:** Meta API token expired
**Fix:** Regenerate token at developers.facebook.com and update `.env` file

### "No insights data available"
**Problem:** No ad data for the specified period
**Fix:** Check if campaigns ran during that time, or adjust `--days` parameter

### "Slack webhook failed"
**Problem:** Can't send to Slack
**Fix:** Verify `SLACK_WEBHOOK_URL` in `.env` is correct and active

---

## When to Use Which Skill

| Situation | Use This |
|-----------|----------|
| Morning check-in | `/meta-ads-quick` |
| Weekly review meeting | `/meta-ads-analyze` |
| Preparing presentation | `/meta-ads-analyze` |
| Facebook ads appearing | `/meta-ads-audit` |
| Budget review | `/meta-ads-analyze` |
| Quick spend check | `/meta-ads-quick --days 1` |
| Performance troubleshooting | `/meta-ads-analyze --ai on` |
| Platform configuration | `/meta-ads-audit` |

---

## Understanding Output

### Quick Report
- **Total Spend:** Your ad spend for the period
- **Impressions:** How many times ads were shown
- **Reach:** Unique people who saw ads
- **Clicks:** Number of clicks on ads
- **CTR:** Click-through rate (clicks ÷ impressions)

### Analyze Report
- **🔴 Critical Alerts:** Campaigns losing money
- **🏆 Conversion Winners:** Best performing campaigns
- **📊 Immediate Actions:** Specific recommendations
- **Traffic Chart:** Visual of impressions/clicks/spend
- **Conversion Chart:** Visual of installs/registrations/purchases

### Audit Report
- **🟢 ACTIVE:** Campaign is running
- **🟡 PAUSED:** Campaign is paused
- **Publisher Platforms: instagram** = Instagram-only ✅
- **Publisher Platforms: Automatic** = All platforms ⚠️
- **🔴 FACEBOOK IS ENABLED** = Action needed

---

## Best Practices

### Daily
- Run `/meta-ads-quick` every morning
- Check for significant spend changes
- Monitor CTR trends

### Weekly
- Run `/meta-ads-analyze` on Monday
- Review AI recommendations
- Check conversion metrics (CPI, CPR, CPA)
- Share charts in team meetings

### Monthly
- Deep-dive with `/meta-ads-analyze --range 30d`
- Compare month-over-month trends
- Review platform configuration with `/meta-ads-audit`

### When Issues Arise
- Facebook ads appearing → `/meta-ads-audit`
- High spend, low conversions → `/meta-ads-analyze --ai on`
- Need quick answer → `/meta-ads-quick`

---

## Tips

1. **Save time:** Default settings work for 90% of use cases
2. **Slack reports:** Check your Slack channel for delivered reports
3. **First run:** Initial `/meta-ads-analyze` has no trends (need 2+ runs)
4. **Multiple accounts:** Use `--account upsc` for UPSC data
5. **Faster analysis:** Use `--ai off` if you don't need AI insights

---

## Getting Help

1. **Check documentation:** Read `skills/README.md` for full details
2. **View help:** Run any skill with `--help` flag
3. **Check logs:** Look in `logs/` directory for error details
4. **Test connection:** Run `/meta-ads-audit` to verify API access

---

## Examples by Use Case

### Morning Standup
```bash
/meta-ads-quick --days 1
```
Shows yesterday's performance in 30 seconds.

### Monday Team Meeting
```bash
/meta-ads-analyze
```
Full analysis with charts to share in presentation.

### Budget Review
```bash
/meta-ads-quick --days 30
/meta-ads-analyze --range 30d
```
Compare quick summary with detailed conversion metrics.

### Troubleshooting High Spend
```bash
/meta-ads-analyze --ai on
```
Get AI recommendations on what to pause/optimize.

### Platform Configuration Issue
```bash
/meta-ads-audit
```
Check which campaigns run on Facebook vs Instagram.

### Quick Performance Check
```bash
/meta-ads-quick --days 7
```
Default 7-day overview, fastest way to check performance.

---

## Key Metrics Explained

- **CPI (Cost Per Install):** How much you pay for each app install
- **CPR (Cost Per Registration):** Cost for each user registration
- **CPA (Cost Per Action/Acquisition):** Cost for each conversion
- **CTR (Click-Through Rate):** Percentage of people who click after seeing ad
- **CPM (Cost Per Mille):** Cost per 1,000 impressions

**Good performance:**
- CTR > 1%
- CPI < ₹50
- CPR < ₹100
- Spend with high conversions

---

## Security Notes

- Never share access tokens publicly
- Keep `.env` files secure
- Rotate access tokens regularly
- Monitor API usage to prevent abuse

---

**Need more details?** See `skills/README.md` for comprehensive documentation.

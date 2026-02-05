# Meta Ads Slack Reporter

Automated Meta (Facebook) Ads performance reporting with Slack notifications.

## Features

- **Daily Performance Metrics**: Impressions, reach, spend, clicks, CTR
- **Multi-Level Reporting**: Campaign, Ad Set, and Individual Ad performance
- **Configurable Detail Levels**: Choose how much detail you want
- **Campaign Status Tracking**: Active, paused, and archived campaigns
- **Top Performers**: Top campaigns, ad sets, and ads by spend
- **Slack Integration**: Formatted reports sent directly to Slack
- **Separate Account Reports**: Independent reports for UPSC and GRE

## Setup

### 1. Install Dependencies

```bash
cd ~/analytics/meta-slack-reporting
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Get Meta API Credentials

#### Step 1: Create/Access Meta App
1. Go to [Meta for Developers](https://developers.facebook.com)
2. Click "My Apps" → "Create App"
3. Select "Business" as app type
4. Fill in app details and create

#### Step 2: Add Marketing API
1. In your app dashboard, click "Add Product"
2. Find "Marketing API" and click "Set Up"

#### Step 3: Generate Access Token
1. Go to **Tools** → **Graph API Explorer**
2. Select your app from dropdown
3. Click "Permissions" and add:
   - `ads_read`
   - `ads_management` (optional, for future features)
4. Click "Generate Access Token"
5. **Important**: Extend to long-lived token (60 days)
   - Use [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)
   - Click "Extend Access Token"
   - Copy the extended token

#### Step 4: Get Ad Account ID
1. Go to [Meta Ads Manager](https://business.facebook.com/adsmanager)
2. Click **Settings** (gear icon)
3. Find **Ad Account ID** (format: `123456789012345`)
4. Add `act_` prefix → `act_123456789012345`

### 3. Configure Environment

```bash
cp .env.example .env
nano .env
```

Update with your credentials:
```bash
META_ADS_ACCOUNT_ID=act_123456789012345
META_ACCESS_TOKEN=your_long_lived_access_token_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
REPORT_DAYS=7
TZ=Asia/Kolkata
ACCOUNT_NAME=PrepAiro UPSC
DETAIL_LEVEL=detailed  # Options: summary, detailed, full
```

**Secure the file:**
```bash
chmod 600 .env
```

### 4. Get Slack Webhook URL

1. Go to [Slack API: Incoming Webhooks](https://api.slack.com/messaging/webhooks)
2. Click "Create New App" → "From scratch"
3. Enable "Incoming Webhooks"
4. Click "Add New Webhook to Workspace"
5. Select channel (e.g., `#analytics` or `#marketing`)
6. Copy webhook URL

## Usage

### Manual Run

```bash
cd ~/analytics/meta-slack-reporting
source venv/bin/activate
python3 meta_ads_reporter.py
```

### Configure Report Detail Level

Edit `.env` and change `DETAIL_LEVEL`:

**`DETAIL_LEVEL=summary`** - Campaigns only (fastest)
- Account summary
- Top 5 campaigns

**`DETAIL_LEVEL=detailed`** - Campaigns + Ad Sets (recommended)
- Account summary
- Top 5 campaigns
- Top 10 ad sets by spend

**`DETAIL_LEVEL=full`** - Everything (most comprehensive)
- Account summary
- Top 5 campaigns
- Top 10 ad sets by spend
- Top 10 individual ads by spend

### Test with Specific Date Range

Edit `.env` and change `REPORT_DAYS`:
```bash
REPORT_DAYS=1   # Yesterday only
REPORT_DAYS=7   # Last week (default)
REPORT_DAYS=30  # Last 30 days
```

## Scheduled Execution (Cron)

Add to crontab for daily reports:

```bash
crontab -e
```

Add this line:
```bash
# Daily Meta Ads report at 9:00 AM IST (3:30 AM UTC)
30 3 * * * cd /home/ec2-user/analytics/meta-slack-reporting && source venv/bin/activate && python3 meta_ads_reporter.py >> logs/cron.log 2>&1
```

### Other Scheduling Options

```bash
# Every 12 hours (9 AM and 9 PM IST)
30 3,15 * * * cd ~/analytics/meta-slack-reporting && source venv/bin/activate && python3 meta_ads_reporter.py >> logs/cron.log 2>&1

# Twice daily (6 AM and 6 PM IST)
30 0,12 * * * cd ~/analytics/meta-slack-reporting && source venv/bin/activate && python3 meta_ads_reporter.py >> logs/cron.log 2>&1

# Weekly (Monday 9 AM IST)
30 3 * * 1 cd ~/analytics/meta-slack-reporting && source venv/bin/activate && python3 meta_ads_reporter.py >> logs/cron.log 2>&1
```

## Slack Report Format

```
┌─────────────────────────────────────┐
│  📊 Meta Ads Performance Report     │
│  Last 7 Days                        │
│  Jan 28 to Feb 4, 2026              │
└─────────────────────────────────────┘

🎯 Campaign Summary
Total Spend: ₹12,450
Total Impressions: 125.3K
Total Reach: 45.2K
Total Clicks: 1.2K (CTR: 0.98%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Top Campaigns (by spend)

1. PrepAiro - UPSC 2026 [🟢 ACTIVE]
   Spend: ₹5,200 | Impressions: 52.0K
   Reach: 18.5K | Clicks: 450 (0.87%)

2. PrepAiro - Mock Tests [🟡 PAUSED]
   Spend: ₹3,800 | Impressions: 38.0K
   Reach: 14.2K | Clicks: 380 (1.00%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Daily Breakdown (Last 7 Days)

Feb 4: ₹1,850 | 18.5K imp | 520 clicks
Feb 3: ₹1,920 | 19.2K imp | 485 clicks
Feb 2: ₹1,780 | 17.8K imp | 445 clicks
```

## Status Indicators

- 🟢 **ACTIVE** - Campaign is running
- 🟡 **PAUSED** - Campaign is paused
- ⏸️ **CAMPAIGN_PAUSED** / **ADSET_PAUSED** - Parent paused
- 🔴 **DISAPPROVED** / **DELETED** - Campaign issues
- ⏳ **PENDING_REVIEW** / **IN_PROCESS** - Processing

## Logs

Logs are stored in `logs/meta_ads_YYYYMMDD.log`

**View today's logs:**
```bash
tail -f logs/meta_ads_$(date +%Y%m%d).log
```

**View cron logs:**
```bash
tail -f logs/cron.log
```

## Troubleshooting

### "Invalid OAuth access token"
- Your access token expired (they last 60 days)
- Generate a new long-lived token from Graph API Explorer

### "Unsupported get request"
- Check your Ad Account ID format: `act_123456789012345`
- Verify the account exists in your Business Manager

### "Error code 190"
- Token is invalid or expired
- Regenerate access token with proper permissions

### No data in report
- Check date range (REPORT_DAYS)
- Verify campaigns were active during the period
- Check if ad account has spend in the timeframe

### Slack webhook fails
- Verify webhook URL is correct
- Check if webhook is still active in Slack
- Test webhook: `curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' YOUR_WEBHOOK_URL`

## Deployment to EC2

```bash
# 1. Copy folder to EC2
scp -i ~/Downloads/ec2_prod.pem -r ~/analytics/meta-slack-reporting ec2-user@65.2.55.151:/home/ec2-user/analytics/

# 2. SSH to server
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151

# 3. Setup
cd /home/ec2-user/analytics/meta-slack-reporting
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod 600 .env

# 4. Test run
python3 meta_ads_reporter.py

# 5. Add to crontab
crontab -e
# (paste cron line from above)
```

## Future Enhancements

- [ ] Ad Set level breakdown
- [ ] Individual ad performance
- [ ] Week-over-week comparison
- [ ] Conversion tracking integration
- [ ] Budget pacing alerts
- [ ] Multiple ad account support
- [ ] Custom metric thresholds

## Support

**Issues:** Report at the analytics repository

**Documentation:** [Meta Marketing API Docs](https://developers.facebook.com/docs/marketing-apis)

---

**Version:** 1.0
**Last Updated:** 2026-02-04

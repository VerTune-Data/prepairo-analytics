# PrepAiro Analytics & Monitoring

Automated analytics and monitoring suite for PrepAiro.

## Projects

### 📊 [Conversion Analytics](./conversion-analytics/)

Automated conversion reporting with Slack notifications.

**Features:**
- 5 daily reports (4x 6-hour + 1x daily summary)
- Channel attribution (Google Ads, Meta, Telegram, etc.)
- Drop-off analysis by channel
- 💎 CONVERTED indicator for premium users
- IST timezone with AM/PM format

**Quick Start:**
```bash
cd conversion-analytics
python3 prepairo_analytics.py 6  # Last 6 hours
```

[📖 Full Documentation](./conversion-analytics/README.md)

---

### ⏱️ [Clicko Uptime Monitor](./clicko-monitor/)

24/7 uptime monitoring for https://clicko.prepairo.ai

**Features:**
- Checks every 5 minutes
- Monitors response time, SSL certificates, server errors
- Smart Slack alerts with cooldowns
- Detects: downtime, timeouts, slow responses, SSL issues

**Quick Start:**
```bash
cd clicko-monitor
export $(grep -v "^#" .env | xargs)
python3 clicko_uptime_monitor.py
```

[📖 Full Documentation](./clicko-monitor/README.md)

---

## Deployment

**EC2 Server:** `65.2.55.151`
**SSH Key:** `~/Downloads/ec2_prod.pem`

### Deploy All

```bash
# Deploy to EC2
scp -i ~/Downloads/ec2_prod.pem -r ~/analytics ec2-user@65.2.55.151:/home/ec2-user/

# SSH and setup
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151

# Setup conversion analytics
cd /home/ec2-user/analytics/conversion-analytics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod 600 .env

# Setup clicko monitor (uses same venv or system python)
cd /home/ec2-user/analytics/clicko-monitor
chmod +x clicko_uptime_monitor.py
chmod 600 .env
```

### Cron Jobs

```bash
crontab -e

# Conversion Analytics - 4x 6-hour reports
30 17 * * * cd /home/ec2-user/analytics/conversion-analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1
30 23 * * * cd /home/ec2-user/analytics/conversion-analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1
30 5 * * * cd /home/ec2-user/analytics/conversion-analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1
30 11 * * * cd /home/ec2-user/analytics/conversion-analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1

# Conversion Analytics - Daily summary
30 6 * * * cd /home/ec2-user/analytics/conversion-analytics && source venv/bin/activate && python3 prepairo_analytics.py 24 12 >> logs/cron.log 2>&1

# Clicko Uptime Monitor - Every 5 minutes
*/5 * * * * cd /home/ec2-user/analytics/clicko-monitor && export $(grep -v "^#" .env | xargs) && python3 clicko_uptime_monitor.py >> logs/cron.log 2>&1
```

## Repository Structure

```
analytics/
├── README.md                     # This file
├── DEPLOYMENT_PLAN.md            # Detailed deployment guide
├── CLAUDE.md                     # Project instructions
│
├── conversion-analytics/         # PrepAiro conversion reports
│   ├── prepairo_analytics.py
│   ├── .env (gitignored)
│   ├── .env.example
│   ├── requirements.txt
│   ├── README.md
│   └── logs/
│
└── clicko-monitor/               # Clicko uptime monitoring
    ├── clicko_uptime_monitor.py
    ├── .env (gitignored)
    ├── .env.example
    ├── .gitignore
    ├── README.md
    └── logs/
```

## Quick Commands

```bash
# SSH to server
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151

# View analytics logs
tail -f /home/ec2-user/analytics/conversion-analytics/logs/analytics_$(date +%Y%m%d).log

# View uptime monitor logs
tail -f /home/ec2-user/analytics/clicko-monitor/logs/clicko_monitor_$(date +%Y%m%d).log

# View cron logs
tail -f /home/ec2-user/analytics/conversion-analytics/logs/cron.log
tail -f /home/ec2-user/analytics/clicko-monitor/logs/cron.log

# Check cron jobs
crontab -l

# Manual run - Analytics
cd /home/ec2-user/analytics/conversion-analytics
source venv/bin/activate
python3 prepairo_analytics.py 6

# Manual run - Uptime Monitor
cd /home/ec2-user/analytics/clicko-monitor
export $(grep -v "^#" .env | xargs)
python3 clicko_uptime_monitor.py
```

## Version History

- **v2.1** - Analytics enhancements (drop-offs, daily summary, improved formatting)
- **v2.0** - Rewrite with 6-message format and channel attribution
- **v1.0** - Clicko uptime monitoring added

## Support

**Issues:** https://github.com/VerTune-Data/prepairo-analytics/issues

---

**Organization:** VerTune Data
**Last Updated:** 2026-02-04

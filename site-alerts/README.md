# PrepaIro Site Uptime Monitor

Automated health monitoring for all PrepaIro sites with Slack alerts.

## Sites Monitored

| Site | URL |
|------|-----|
| UPSC PrepAiro | https://upsc.prepairo.ai |
| UPSC Web PrepAiro | https://upsc.web.prepairo.ai |
| GRE PrepAiro | https://gre.prepairo.ai |
| PrepAiro Main | https://prepairo.ai |

## Checks Performed

- **DNS Resolution** - Verifies domain resolves correctly
- **SSL Certificate** - Validates certificate and checks expiry (<30 days warning)
- **HTTP Status** - Checks for expected 200 response
- **Response Time** - Alerts if response >3 seconds
- **Content Validation** - Verifies HTML content type and non-empty response
- **Connection Errors** - Detects unreachable sites
- **Timeout Detection** - Alerts if no response within 15 seconds

## Setup

### 1. Install Dependencies

```bash
cd ~/site-alerts
pip install requests
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Slack webhook URL
```

### 3. Test Locally

```bash
export $(cat .env | xargs)
python3 site_uptime_monitor.py
```

## Deployment to EC2

### 1. Copy Files to Server

```bash
scp -i ~/Downloads/ec2_prod.pem -r ~/site-alerts ec2-user@65.2.55.151:/home/ec2-user/
```

### 2. Setup on EC2

```bash
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151

cd /home/ec2-user/site-alerts
chmod +x site_uptime_monitor.py
chmod 600 .env
```

### 3. Add to Crontab

```bash
crontab -e

# Add this line (runs every 5 minutes):
*/5 * * * * cd /home/ec2-user/site-alerts && export $(cat .env | xargs) && python3 site_uptime_monitor.py >> logs/cron.log 2>&1
```

## Alert Types

### Critical (immediate)
- **DNS Failure** - Domain cannot be resolved
- **Site DOWN** - Connection refused/failed
- **Timeout** - No response within 15 seconds
- **Server Error** - HTTP 5xx status codes
- **Client Error** - HTTP 4xx status codes
- **SSL Invalid** - Certificate validation failure

### Warning
- **SSL Expiring** - Certificate expires in <30 days
- **Slow Response** - Response time >3 seconds
- **Empty Response** - Suspiciously small page content
- **Unexpected Content Type** - Non-HTML response
- **Unexpected Redirect** - 3xx when 200 expected

## Monitoring

### View Logs

```bash
# Today's log
tail -f ~/site-alerts/logs/site_monitor_$(date +%Y%m%d).log

# Cron log
tail -f ~/site-alerts/logs/cron.log
```

### Manual Check

```bash
cd ~/site-alerts
export $(cat .env | xargs)
python3 site_uptime_monitor.py
```

## File Structure

```
site-alerts/
├── site_uptime_monitor.py      # Main monitoring script
├── .env                         # Configuration (not in git)
├── .env.example                # Example configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── logs/                       # Log files (auto-created)
│   ├── site_monitor_YYYYMMDD.log
│   └── cron.log
└── .site_monitor_state.json    # Alert cooldown state
```

## Troubleshooting

### No Alerts Received

```bash
# Check if script is running
grep "site_uptime_monitor" /var/log/cron

# Check logs
tail -50 ~/site-alerts/logs/site_monitor_$(date +%Y%m%d).log

# Test Slack webhook manually
curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"Test from Site Monitor"}' \
  $SLACK_WEBHOOK_SITE_ALERTS
```

## License

Proprietary - VerTune Data

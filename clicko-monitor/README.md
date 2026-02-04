# Clicko Uptime Monitor

Automated uptime monitoring for https://clicko.prepairo.ai with Slack alerts.

## Features

- ✅ **Continuous Monitoring** - Checks every 5 minutes
- 🚨 **Smart Alerts** - Only alerts on issues, with cooldown to avoid spam
- 📊 **Comprehensive Checks**:
  - Uptime/Downtime detection
  - Response time monitoring
  - SSL certificate validation
  - SSL expiry warnings (30 days before)
  - HTTP error detection (5xx)
  - Timeout detection (>10s)
  - Slow response alerts (>3s)

## Setup

### 1. Install Dependencies

```bash
cd ~/clicko-monitor
pip install requests
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Slack webhook URL
```

### 3. Test Locally

```bash
# Load environment and test
export $(cat .env | xargs)
python3 clicko_uptime_monitor.py
```

## Deployment to EC2

### 1. Copy Files to Server

```bash
scp -i ~/Downloads/ec2_prod.pem -r ~/clicko-monitor ec2-user@65.2.55.151:/home/ec2-user/
```

### 2. Setup on EC2

```bash
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151

cd /home/ec2-user/clicko-monitor
chmod +x clicko_uptime_monitor.py
chmod 600 .env
```

### 3. Add to Crontab

```bash
crontab -e

# Add this line:
*/5 * * * * cd /home/ec2-user/clicko-monitor && export $(cat .env | xargs) && python3 clicko_uptime_monitor.py >> logs/cron.log 2>&1
```

## Alert Types

### 🔴 Critical Alerts (15 min cooldown)
- **Down**: Connection failures
- **Timeout**: No response within 10 seconds
- **Server Error**: HTTP 5xx status codes

### 🔒 SSL Alerts
- **SSL Error**: Certificate validation failures (60 min cooldown)
- **Expiring Soon**: Certificate expires in <30 days (daily alert)

### 🐌 Performance Alerts (30 min cooldown)
- **Slow Response**: Response time >3 seconds

## Monitoring

### View Logs

```bash
# Today's log
tail -f ~/clicko-monitor/logs/clicko_monitor_$(date +%Y%m%d).log

# Cron log
tail -f ~/clicko-monitor/logs/cron.log
```

### Check Status

```bash
# Manual check
cd ~/clicko-monitor
export $(cat .env | xargs)
python3 clicko_uptime_monitor.py
```

## Configuration

Edit `.env` to customize:

```bash
# URL to monitor
CLICKO_URL=https://clicko.prepairo.ai

# Slack webhook
SLACK_WEBHOOK_UPTIME=your_webhook_url
```

Edit thresholds in `clicko_uptime_monitor.py`:

```python
SLOW_RESPONSE_THRESHOLD = 3.0  # seconds
TIMEOUT = 10  # seconds
```

## File Structure

```
clicko-monitor/
├── clicko_uptime_monitor.py  # Main monitoring script
├── .env                       # Configuration (not in git)
├── .env.example              # Example configuration
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── logs/                     # Log files (auto-created)
│   ├── clicko_monitor_YYYYMMDD.log
│   └── cron.log
└── .clicko_monitor_state.json  # Alert cooldown state
```

## How It Works

1. **Every 5 minutes**, cron executes the script
2. Script makes HTTP request to Clicko URL
3. Checks:
   - Response time
   - HTTP status code
   - SSL certificate validity
   - SSL expiry date
4. If issue detected, sends Slack alert (with cooldown)
5. Logs all checks to daily log file

## Troubleshooting

### No Alerts Received

```bash
# Check if script is running
grep "clicko_uptime_monitor" /var/log/cron

# Check logs
tail -50 ~/clicko-monitor/logs/clicko_monitor_$(date +%Y%m%d).log

# Test Slack webhook manually
curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"Test from Clicko Monitor"}' \
  $SLACK_WEBHOOK_UPTIME
```

### Environment Variables Not Loading

Make sure cron command includes:
```bash
export $(cat .env | xargs) &&
```

## License

Proprietary - VerTune Data

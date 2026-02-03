# PrepAiro Analytics - Deployment Plan

## 📋 Overview

Automated analytics script that tracks subscription metrics and sends reports to Slack at scheduled intervals.

**What it tracks:**
- New phone-based signups (with name, email, phone)
- Subscribe Now button clicks
- Conversion funnel (Plus clicks → Subscribe clicks → Payment screen → Subscriptions)
- Referral usage and conversions

**When it runs:**
- 11:00 PM IST (5:30 PM UTC) - End of day report
- 5:00 AM IST (11:30 PM UTC) - Morning report
- 12:00 PM IST (6:30 AM UTC) - Midday update

---

## 🎯 Deployment Steps

### **1. Local Testing (Do this first!)**

```bash
# Navigate to analytics directory
cd ~/analytics

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test the script (fetches last 1 hour of data)
python3 prepairo_analytics.py 1

# Check the logs
tail -f logs/analytics_$(date +%Y%m%d).log
```

**Expected output:**
- Database connection successful
- Data fetched with counts
- Slack message sent
- Check your Slack channel for the report!

---

### **2. Deploy to EC2 Production Server**

#### **Step 2.1: Copy files to EC2**

```bash
# From your local machine
scp -i ~/Downloads/ec2_prod.pem -r ~/analytics ec2-user@65.2.55.151:/home/ec2-user/
```

#### **Step 2.2: SSH into EC2 and setup**

```bash
# SSH into server
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151

# Navigate to analytics directory
cd /home/ec2-user/analytics

# Install system dependencies (if not already installed)
sudo yum install -y python3 python3-pip postgresql-devel gcc

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Make script executable
chmod +x prepairo_analytics.py

# Secure .env file
chmod 600 .env
chown ec2-user:ec2-user .env
```

#### **Step 2.3: Test on EC2**

```bash
# Test with last 1 hour
source venv/bin/activate
python3 prepairo_analytics.py 1

# View logs
tail -f logs/analytics_$(date +%Y%m%d).log
```

---

### **3. Setup Cron Schedule**

```bash
# Edit crontab
crontab -e

# Add these lines (press 'i' to insert mode in vim):

# Analytics Reports - 11 PM IST (17:30 UTC)
30 17 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 24 >> logs/cron.log 2>&1

# Analytics Reports - 5 AM IST (23:30 UTC previous day)
30 23 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 24 >> logs/cron.log 2>&1

# Analytics Reports - 12 PM IST (06:30 UTC)
30 6 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 12 >> logs/cron.log 2>&1

# Press ESC, then type :wq and press ENTER to save and quit
```

#### **Verify cron setup:**

```bash
# List current cron jobs
crontab -l

# Test cron manually (simulates cron execution)
cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 1 >> logs/cron.log 2>&1

# View cron logs
tail -f /home/ec2-user/analytics/logs/cron.log
```

---

## 📊 Database Queries Explained

### **Query 1: New Phone Signups**
- Joins `users_profile`, `users_auth`, and `user_subscriptions`
- Filters for phone-verified users
- Shows subscription status (Subscribed or Free)
- Includes name, phone, email

### **Query 2: Subscribe Now Button Clicks**
- Tracks `subscribe_now_audit` table
- Shows which users clicked the button
- Includes plan type, pricing
- Shows conversion status (whether they completed payment)

### **Query 3: Conversion Funnel**
- Counts clicks at each stage:
  - Plus page views (`plus_click_audit`)
  - Subscribe Now clicks (`subscribe_now_audit`)
  - Payment screen views (`payment_option_screen_audit`)
  - Successful subscriptions (`user_subscriptions`)
- Calculates conversion rate

### **Query 4: Referral Tracking**
- Tracks referral code usage
- Shows influencer attribution
- Displays conversion and revenue

---

## 🔍 Monitoring & Maintenance

### **View Logs**

```bash
# Today's analytics log
tail -f /home/ec2-user/analytics/logs/analytics_$(date +%Y%m%d).log

# Cron execution log
tail -f /home/ec2-user/analytics/logs/cron.log

# Last 50 lines of analytics log
tail -50 /home/ec2-user/analytics/logs/analytics_$(date +%Y%m%d).log
```

### **Manual Execution**

```bash
# Run for last 24 hours
cd /home/ec2-user/analytics
source venv/bin/activate
python3 prepairo_analytics.py 24

# Run for last 7 days (weekly report)
python3 prepairo_analytics.py 168

# Run for last hour (testing)
python3 prepairo_analytics.py 1
```

### **Troubleshooting**

#### **Database Connection Issues:**
```bash
# Test database connection manually
psql -h prod-beta.cdk0yuaiebcw.ap-south-1.rds.amazonaws.com \
     -U postgres \
     -d postgres \
     -c "SET search_path TO app; SELECT COUNT(*) FROM users_profile;"
```

#### **Slack Webhook Issues:**
```bash
# Test Slack webhook
curl -X POST -H 'Content-Type: application/json' \
     -d '{"text":"Test message from analytics script"}' \
     https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### **Cron Not Running:**
```bash
# Check cron service status
sudo systemctl status crond

# Check system logs for cron
sudo tail -f /var/log/cron

# Verify cron has correct timezone
timedatectl
```

---

## 🔒 Security Notes

1. **Environment Variables**: Database credentials stored in `.env` file with restricted permissions (600)
2. **Read-Only Queries**: All queries are SELECT only, no data modification
3. **Connection Pooling**: Each run opens and closes connection (no persistent connections)
4. **Error Handling**: Failures are logged and sent to Slack for immediate notification

---

## 📈 Customization

### **Change Report Schedule**

Edit crontab and adjust the times. Cron uses UTC timezone.

**IST to UTC conversion:**
- 11:00 PM IST = 17:30 UTC
- 5:00 AM IST = 23:30 UTC (previous day)
- 12:00 PM IST = 06:30 UTC

### **Modify Queries**

Edit `prepairo_analytics.py` and update the SQL queries in the `get_analytics_data()` function.

### **Change Slack Message Format**

Modify the `format_slack_message()` function to customize the Slack report layout.

### **Add New Metrics**

1. Add a new query in `get_analytics_data()`
2. Update `format_slack_message()` to display the new data
3. Test locally before deploying

---

## ✅ Checklist

**Before Deployment:**
- [ ] Tested locally successfully
- [ ] Verified database connection
- [ ] Confirmed Slack webhook works
- [ ] Reviewed all queries for correctness

**After Deployment:**
- [ ] Files copied to EC2
- [ ] Dependencies installed
- [ ] Test run successful on EC2
- [ ] Cron jobs configured
- [ ] First scheduled report received in Slack
- [ ] Logs are being written correctly

---

## 🆘 Support

**Common Issues:**

1. **"No module named psycopg2"**: Virtual environment not activated
2. **"Connection refused"**: Database host/port incorrect or firewall blocking
3. **"Slack webhook failed"**: Check webhook URL is correct
4. **"Cron not running"**: Check cron syntax and permissions

**Getting Help:**
- Check logs first: `tail -f logs/analytics_$(date +%Y%m%d).log`
- Verify database connectivity
- Test Slack webhook manually
- Check cron logs: `tail -f logs/cron.log`

---

## 📝 File Structure

```
/home/ec2-user/analytics/
├── prepairo_analytics.py    # Main script
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (SECURED)
├── DEPLOYMENT_PLAN.md        # This file
├── venv/                     # Python virtual environment
└── logs/                     # Log files
    ├── analytics_YYYYMMDD.log
    └── cron.log
```

---

## 🎉 Success Criteria

You'll know it's working when:
1. ✅ Slack reports arrive at scheduled times
2. ✅ Reports contain accurate data (verify against database)
3. ✅ No error messages in logs
4. ✅ Cron jobs execute successfully (check `cron.log`)

---

**Deployed by:** Claude Code
**Date:** 2026-02-03
**Version:** 1.0

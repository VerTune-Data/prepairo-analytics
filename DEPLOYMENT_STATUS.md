# ✅ PrepAiro Analytics - Deployment Complete

**Deployment Date:** 2026-02-03
**Server:** 65.2.55.151 (Production EC2)
**Status:** 🟢 LIVE & OPERATIONAL

---

## 📊 Test Results

### ✅ Initial Test Run (Last 1 Hour)
```
✅ Database Connection: SUCCESS
   - Host: prod-beta.cdk0yuaiebcw.ap-south-1.rds.amazonaws.com
   - Total Users in DB: 111,338

✅ Data Fetched:
   - 2 new signups
   - 1 subscribe button click
   - 0 referrals

✅ Slack Notification: SENT SUCCESSFULLY
```

### ✅ System Checks
- [x] Python 3.9 installed
- [x] PostgreSQL client libraries installed
- [x] Virtual environment created
- [x] All dependencies installed
- [x] Database connectivity verified
- [x] Slack webhook verified
- [x] Cron service running
- [x] Cron jobs configured

---

## ⏰ Automated Schedule

Your analytics reports will be sent to Slack at:

| Time (IST) | Time (UTC) | Report Type | Lookback Period |
|------------|------------|-------------|-----------------|
| 11:00 PM   | 5:30 PM    | End of Day  | Last 24 hours   |
| 5:00 AM    | 11:30 PM   | Morning     | Last 24 hours   |
| 12:00 PM   | 6:30 AM    | Midday      | Last 12 hours   |

---

## 📈 What Gets Tracked

### 1. **New Signups**
- Phone-verified users
- Name, email, phone number
- Subscription status (Free or Subscribed)

### 2. **Subscribe Now Clicks**
- Users who clicked the "Subscribe Now" button
- Plan selected (Monthly/Yearly)
- Price information (original + discounted)
- Conversion status (Converted or Pending)

### 3. **Conversion Funnel**
- Plus page clicks
- Subscribe Now button clicks
- Payment screen views
- Successful subscriptions
- Conversion rate calculation

### 4. **Referral Tracking**
- Referral code usage
- Influencer attribution
- Conversion status
- Revenue generated

---

## 🔍 How to Monitor

### View Real-time Logs
```bash
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151
cd /home/ec2-user/analytics

# Watch today's analytics log
tail -f logs/analytics_$(date +%Y%m%d).log

# Watch cron execution log
tail -f logs/cron.log
```

### Run Manual Report
```bash
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151
cd /home/ec2-user/analytics
source venv/bin/activate

# Last 24 hours
python3 prepairo_analytics.py 24

# Last 7 days (weekly report)
python3 prepairo_analytics.py 168

# Last 1 hour (testing)
python3 prepairo_analytics.py 1
```

---

## 🛠 Useful Commands

### Check Cron Jobs
```bash
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151
crontab -l
```

### Check Cron Service
```bash
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151
sudo systemctl status crond
```

### View Recent Slack Messages
Check your Slack channel for analytics reports!

### Test Database Connection
```bash
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151
psql -h prod-beta.cdk0yuaiebcw.ap-south-1.rds.amazonaws.com \
     -U postgres \
     -d postgres \
     -c "SET search_path TO app; SELECT COUNT(*) FROM users_profile;"
```

---

## 📂 File Locations

### On EC2 Server
```
/home/ec2-user/analytics/
├── prepairo_analytics.py     # Main script
├── requirements.txt           # Python dependencies
├── .env                       # Configuration (SECURED)
├── DEPLOYMENT_PLAN.md         # Full documentation
├── README.md                  # Quick reference
├── venv/                      # Python virtual environment
└── logs/                      # All logs stored here
    ├── analytics_YYYYMMDD.log
    └── cron.log
```

### On Local Machine
```
~/analytics/
└── (Same structure, for reference/updates)
```

---

## 🚨 Troubleshooting

### No Slack Message Received?
1. Check logs: `tail -f /home/ec2-user/analytics/logs/analytics_$(date +%Y%m%d).log`
2. Verify webhook URL in `.env` file
3. Test webhook manually (see DEPLOYMENT_PLAN.md)

### Cron Not Running?
1. Check cron service: `sudo systemctl status crond`
2. View cron logs: `tail -f /home/ec2-user/analytics/logs/cron.log`
3. Verify crontab: `crontab -l`

### Database Connection Issues?
1. Check security groups allow EC2 → RDS connection
2. Verify credentials in `.env` file
3. Test connection manually (see commands above)

---

## 🔐 Security Notes

✅ **Configuration Secured**
- `.env` file has 600 permissions (owner read/write only)
- Database credentials stored locally on EC2
- No credentials in code or version control

✅ **Read-Only Operations**
- All queries are SELECT only
- No INSERT/UPDATE/DELETE operations
- Safe to run continuously

✅ **Error Handling**
- All errors logged to file
- Critical errors sent to Slack
- Script fails gracefully

---

## 📝 Next Steps (Optional)

### Add More Metrics
Edit `prepairo_analytics.py` and add queries in the `get_analytics_data()` function.

### Change Schedule
Edit crontab:
```bash
crontab -e
```

### Modify Slack Format
Edit the `format_slack_message()` function in `prepairo_analytics.py`.

### Add Email Reports
Install email libraries and integrate with AWS SES.

---

## ✨ Success Indicators

You'll know it's working when:
1. ✅ Slack reports arrive at scheduled times (11 PM, 5 AM, 12 PM IST)
2. ✅ Reports contain real data from your database
3. ✅ No error messages in logs
4. ✅ Conversion metrics are accurate

---

## 📞 Support

**Log Files:**
- Analytics: `/home/ec2-user/analytics/logs/analytics_YYYYMMDD.log`
- Cron: `/home/ec2-user/analytics/logs/cron.log`

**Documentation:**
- Full guide: `/home/ec2-user/analytics/DEPLOYMENT_PLAN.md`
- Quick reference: `/home/ec2-user/analytics/README.md`

**Test Commands:**
```bash
# Quick test
ssh -i ~/Downloads/ec2_prod.pem ec2-user@65.2.55.151 \
  "cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 1"
```

---

**🎉 Your analytics automation is now LIVE!**

Check your Slack channel - you should have already received a test message!

Next automated report: See schedule above ⬆️

# PrepAiro Analytics

Automated analytics reporting system for PrepAiro that tracks user engagement, conversions, and purchase intents with real-time Slack notifications.

## 🚀 Features

- **6 Automated Slack Reports** sent 4 times daily
- **Channel Attribution** tracking via Play Store referrer and AppsFlyer
- **Conversion Funnel** tracking from Plus page to payment
- **IST Timezone** support for all timestamps
- **Unique User Tracking** for purchase intents
- **Production-Ready** with error handling and logging

## 📊 Reports Generated

### 1. App Installs
- Total installs vs phone verified users
- Platform breakdown (iOS/Android)
- Channel attribution (Google Ads, Instagram, Telegram, etc.)
- UTM campaign tracking

### 2. Conversions
- Total conversions with platform breakdown
- Channel-wise conversion tracking
- Campaign attribution

### 3. Purchase Intents Summary
- Quick metrics dashboard
- Plus page clicks, Subscribe clicks, Payment clicks
- Coupon applications

### 4-6. Detailed User Lists
- Plus Page Clicks with user details
- Subscribe Now Clicks with plan info
- Payment Method Clicks with conversion status

## 🛠️ Setup

### Prerequisites
- Python 3.9+
- PostgreSQL access to production database
- Slack webhook URL

### Installation

1. Clone the repository:
```bash
git clone https://github.com/VerTune-Data/prepairo-analytics.git
cd prepairo-analytics
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. Test locally:
```bash
python3 prepairo_analytics.py 6  # Last 6 hours
```

## 📅 Scheduled Reports

Reports run **4 times daily** at:
- **23:00 IST** (17:30 UTC) - Night Report
- **05:00 IST** (23:30 UTC) - Early Morning Report
- **11:00 IST** (05:30 UTC) - Late Morning Report
- **17:00 IST** (11:30 UTC) - Evening Report

Each report covers the **last 6 hours** of data.

## 🖥️ Production Deployment

### EC2 Server Setup

1. Copy files to server:
```bash
scp -r ~/analytics ec2-user@65.2.55.151:/home/ec2-user/
```

2. SSH into server and setup:
```bash
ssh ec2-user@65.2.55.151
cd /home/ec2-user/analytics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x prepairo_analytics.py
chmod 600 .env
```

3. Configure cron jobs:
```bash
crontab -e
```

Add these lines:
```cron
# Analytics Reports - 23:00 IST (17:30 UTC)
30 17 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1

# Analytics Reports - 05:00 IST (23:30 UTC)
30 23 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1

# Analytics Reports - 11:00 IST (05:30 UTC)
30 5 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1

# Analytics Reports - 17:00 IST (11:30 UTC)
30 11 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1
```

## 📝 Environment Variables

Create a `.env` file with:

```env
DB_HOST=your-database-host.rds.amazonaws.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
DB_SCHEMA=app
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 🔍 Monitoring

### View Logs
```bash
# Today's analytics log
tail -f logs/analytics_$(date +%Y%m%d).log

# Cron execution log
tail -f logs/cron.log
```

### Manual Execution
```bash
cd /home/ec2-user/analytics
source venv/bin/activate

# Last 6 hours
python3 prepairo_analytics.py 6

# Last 24 hours
python3 prepairo_analytics.py 24

# Last 7 days
python3 prepairo_analytics.py 168
```

## 🎯 Channel Attribution

The system parses install referrer data to categorize channels:

- **Google Ads** (Search, Display, App Campaign, Shopping)
- **Meta** (Instagram, Facebook)
- **Telegram**
- **Website**
- **Play Store Organic**
- **Clicko** (with detailed campaign tracking)
- **Direct / Not Set**
- **iOS** (No Attribution)

## 📊 Database Schema

Queries data from these tables:
- `users_profile` - User information and platform tracking
- `users_auth` - Phone verification status
- `user_subscriptions` - Active subscriptions
- `plus_click_audit` - Plus page interactions
- `subscribe_now_audit` - Subscribe button clicks
- `payment_option_screen_audit` - Payment screen views
- `holiday_coupon_applied_audit` - Coupon applications

## 🔧 Customization

### Change Report Frequency
Edit cron schedule to adjust timing.

### Add New Metrics
1. Add query in `get_*_data()` functions
2. Update formatting in `format_*_message()` functions
3. Test locally before deploying

### Modify Slack Format
Edit the `format_*_message()` functions to customize message layout.

## 🛡️ Security

- Database credentials stored in `.env` with 600 permissions
- All queries are read-only (SELECT only)
- No sensitive data in version control
- Proper error handling and logging

## 📄 License

Proprietary - VerTune Data

## 👥 Authors

- **Developed by:** Claude Code
- **Organization:** VerTune Data
- **Project:** PrepAiro

## 🐛 Issues & Support

For issues or questions, contact the development team or create an issue in this repository.

---

**Last Updated:** 2026-02-03
**Version:** 2.0

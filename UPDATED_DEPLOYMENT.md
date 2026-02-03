# 🚀 Updated Analytics - Deployment Complete

**Updated:** 2026-02-03
**Version:** 2.0

---

## ✅ Changes Implemented

### 1. **Schedule Updated**
- **OLD:** 3 reports/day (24h & 12h lookback)
- **NEW:** 4 reports/day (6h lookback each)

### 2. **New Tracking Features**

#### ✅ Platform-wise Signups (iOS vs Android)
- Tracks `signup_platform` field
- Shows counts per platform
- Shows how many subscribed per platform
- **NO individual user details** (just counts)

#### ✅ Coupon Applications
- Tracks `holiday_coupon_applied_audit` table
- Shows total applications
- Shows unique users

#### ✅ Subscription Details
- Full subscription information from `user_subscriptions`
- Start date & expiry date (in IST)
- Plan type, amount, payment source
- Subscription status

#### ✅ User Details Where Needed
- Plus page clicks
- Subscribe Now clicks
- Payment screen views
- Successful subscriptions

#### ❌ Removed
- Individual signup user details (replaced with platform counts)
- Referral usage section

### 3. **IST Timezone**
- All timestamps converted to IST
- Database queries use `AT TIME ZONE 'Asia/Kolkata'`
- Slack messages show IST times

---

## ⏰ New Report Schedule

| Time (IST) | Time (UTC) | Lookback | Next Run |
|------------|------------|----------|----------|
| **00:00** (Midnight) | 18:30 (prev) | 6 hours | Tonightmidnight |
| **06:00** (Morning) | 00:30 | 6 hours | Tomorrow 6 AM |
| **12:00** (Noon) | 06:30 | 6 hours | Tomorrow noon |
| **18:00** (Evening) | 12:30 | 6 hours | Tonight 6 PM |

---

## 📊 What's Tracked Now

### Conversion Funnel
- Plus page clicks
- Subscribe Now clicks
- Payment screen views
- Successful subscriptions
- Conversion rate (%)

### Platform Signups (iOS/Android)
```
👥 New Phone Signups: 150
• iOS: 80 (Subscribed: 12)
• ANDROID: 65 (Subscribed: 8)
• UNKNOWN: 5 (Subscribed: 0)
```

### Coupon Applications
```
🎟️ Coupons Applied: 25 (Unique Users: 23)
```

### User Details Sections
1. **Plus Page Clicks** - Who viewed Plus page
2. **Subscribe Now Clicks** - Who clicked subscribe (with conversion status)
3. **Payment Screen Views** - Who reached payment screen
4. **Successful Subscriptions** - Who actually subscribed (with dates)

---

## 🔍 SQL Query Updates

### Platform Signups Query
```sql
SELECT
    COALESCE(up.signup_platform, 'UNKNOWN') as platform,
    COUNT(*) as signup_count,
    SUM(CASE WHEN us.id IS NOT NULL THEN 1 ELSE 0 END) as subscribed_count
FROM users_profile up
JOIN users_auth ua ON up.id = ua.id
LEFT JOIN user_subscriptions us ON up.id = us.user_id
    AND us.subscription_status = 'ACTIVE'
WHERE ua.is_phone_no_verified = TRUE
    AND up.created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
        >= (NOW() AT TIME ZONE 'Asia/Kolkata' - INTERVAL '6 hours')
GROUP BY up.signup_platform;
```

### Subscriptions Query
```sql
SELECT
    up.full_name,
    up.phone_number,
    ua.email,
    us.plan_type,
    us.amount,
    us.subscription_status,
    us.start_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' as start_date_ist,
    us.expiry_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' as expiry_date_ist,
    us.payment_source,
    us.created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' as created_at_ist
FROM user_subscriptions us
JOIN users_profile up ON us.user_id = up.id
JOIN users_auth ua ON us.user_id = ua.id
WHERE us.created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
    >= (NOW() AT TIME ZONE 'Asia/Kolkata' - INTERVAL '6 hours')
    AND us.subscription_status = 'ACTIVE';
```

### Coupon Applications Query
```sql
SELECT
    COUNT(*) as coupon_count,
    COUNT(DISTINCT user_id) as unique_users
FROM holiday_coupon_applied_audit
WHERE created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
    >= (NOW() AT TIME ZONE 'Asia/Kolkata' - INTERVAL '6 hours');
```

---

## 🧪 Test Results

**Latest test run (6 hours lookback):**
```
✅ Connected to prod-beta RDS
✅ Data fetched: 0 platforms, 0 plus clicks, 0 subscribe clicks, 0 subscriptions
✅ Slack notification sent successfully
```

---

## 📂 Files Updated

### On EC2: `/home/ec2-user/analytics/`
- `prepairo_analytics.py` - Updated with new queries
- Crontab - Updated to 4x daily schedule

### Locally: `~/analytics/`
- `prepairo_analytics.py` - Updated version
- `UPDATED_DEPLOYMENT.md` - This file

---

## 🔄 Cron Jobs

```cron
# 00:00 IST (18:30 UTC) - Midnight
30 18 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1

# 06:00 IST (00:30 UTC) - Morning
30 0 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1

# 12:00 IST (06:30 UTC) - Noon
30 6 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1

# 18:00 IST (12:30 UTC) - Evening
30 12 * * * cd /home/ec2-user/analytics && source venv/bin/activate && python3 prepairo_analytics.py 6 >> logs/cron.log 2>&1
```

---

## 📱 Slack Message Format

### Example Report:
```
📊 PrepAiro Analytics Report (6h)
2026-02-03 18:00 IST

📈 Conversion Funnel
• Plus Page Clicks: 45
• Subscribe Now Clicks: 12
• Payment Screen Views: 8
• Subscriptions: 3
• Conversion Rate: 25.0%

👥 New Phone Signups: 120
• iOS: 70 (Subscribed: 10)
• ANDROID: 45 (Subscribed: 5)
• UNKNOWN: 5 (Subscribed: 0)

🎟️ Coupons Applied: 15 (Unique Users: 14)

➕ Plus Page Clicks: 45
• User Name
  📱 +919876543210 | 📧 user@example.com
  🕐 Feb 03, 05:30 PM IST
...

🎯 Subscribe Now Clicks: 12 (Converted: 3)
• User Name - ✅ Converted
  📱 +919876543210 | 💰 YEARLY - ₹6499.00
  🕐 Feb 03, 05:45 PM IST
...

💳 Payment Screen Views: 8
...

✅ Successful Subscriptions: 3
• User Name - YEARLY
  📱 +919876543210 | 💰 ₹6499
  📅 Start: Feb 03, 2026 | Expires: Feb 03, 2027
  💳 Source: SUBSCRIPTION | Status: ACTIVE
...
```

---

## ✅ Deployment Checklist

- [x] Script updated with new queries
- [x] Platform signup tracking added
- [x] Coupon tracking added
- [x] Subscription details added
- [x] Referral section removed
- [x] Individual signup details removed (replaced with counts)
- [x] IST timezone conversion added
- [x] Deployed to EC2
- [x] Tested successfully
- [x] Cron updated to 4x daily (6h lookback)
- [x] Old cron jobs removed
- [x] Slack notification verified

---

## 🎯 Next Report

Check your Slack channel at:
- **Tonight 18:00 IST** (6 PM)
- **Tonight 00:00 IST** (Midnight)
- **Tomorrow 06:00 IST** (6 AM)
- **Tomorrow 12:00 IST** (Noon)

**Everything is LIVE! 🚀**

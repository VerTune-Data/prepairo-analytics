# PrepAiro Conversion Analytics

Automated analytics reporting for PrepAiro app that tracks conversions, installs, and user engagement with Slack notifications.

## Features

- **8 Automated Reports** - 5 times daily (4x 6-hour + 1x daily summary)
- **Channel Attribution** - Track installs by Google Ads, Meta, Telegram, etc.
- **Conversion Funnel** - From installs → phone verified → conversions
- **Drop-off Analysis** - By channel conversion rates
- **💎 CONVERTED Indicator** - Premium visual for converted users
- **IST Timezone** - All times in 12-hour AM/PM format

## Quick Start

### Local Setup

```bash
cd ~/analytics/conversion-analytics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with database credentials

# Test
python3 prepairo_analytics.py 1  # Last 1 hour
```

### Deployment

See [DEPLOYMENT_PLAN.md](../DEPLOYMENT_PLAN.md) in the root folder.

## Usage

```bash
python3 prepairo_analytics.py <hours> [offset_hours]

# Examples:
python3 prepairo_analytics.py 6      # Last 6 hours
python3 prepairo_analytics.py 24 12  # Yesterday's 24 hours
```

## Reports Generated

1. **App Installs & Drop-offs** - Platform breakdown, channel attribution
2. **Conversions** - Channel-wise conversion tracking
3. **Purchase Intents** - Summary metrics
4. **Subscribe Clicks** - Detailed user list with 💎 CONVERTED
5. **Payment Clicks** - Payment method tracking with 💎 CONVERTED

Total: 8 messages (6 content + 2 delimiters)

## Schedule

| Time (IST) | Type | Command | Window |
|-----------|------|---------|--------|
| 05:00 AM | 6-hour | `py 6` | 11 PM - 5 AM |
| 11:00 AM | 6-hour | `py 6` | 5 AM - 11 AM |
| 12:00 PM | **Daily** | `py 24 12` | **Yesterday 12-12** |
| 17:00 PM | 6-hour | `py 6` | 11 AM - 5 PM |
| 23:00 PM | 6-hour | `py 6` | 5 PM - 11 PM |

## Documentation

- Main README: [../README.md](../README.md)
- Deployment: [../DEPLOYMENT_PLAN.md](../DEPLOYMENT_PLAN.md)
- Claude Instructions: [../CLAUDE.md](../CLAUDE.md)

#!/usr/bin/env python3
"""
PrepAiro Analytics - 3-Message Format
- Message 1: App Installs with channel attribution
- Message 2: Conversions with channel breakdown
- Message 3: Raw records of Subscribe Now clicks
"""

import os
import sys
import psycopg2
import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import logging
from urllib.parse import parse_qs, urlparse

# Load .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'options': f'-c search_path={os.getenv("DB_SCHEMA", "app")}'
}

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

# Logging setup
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f'analytics_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info(f"✅ Connected to {DB_CONFIG['host']}")
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise


def execute_query(conn, query: str) -> List[Dict]:
    """Execute query and return results as list of dicts"""
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        return results
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return []


def to_ist(utc_datetime) -> datetime:
    """Convert UTC datetime to IST for display (adds 5:30 hours)"""
    if isinstance(utc_datetime, datetime):
        return utc_datetime + timedelta(hours=5, minutes=30)
    return utc_datetime


def extract_param(query_string: str, param_name: str) -> Optional[str]:
    """Extract parameter value from URL query string"""
    try:
        params = parse_qs(query_string)
        return params.get(param_name, [None])[0]
    except:
        # Fallback to regex
        pattern = f"{param_name}=([^&]*)"
        match = re.search(pattern, query_string)
        return match.group(1) if match else None


def parse_install_channel(play_refer_data: dict) -> str:
    """
    Parse install channel from play_refer JSONB data.
    Mimics the backend SlackNotificationUtil logic.
    """
    try:
        if not play_refer_data:
            return "No Tracking"

        # Check if there's an attribution object (AppsFlyer/Clicko data)
        if 'attribution' in play_refer_data:
            attribution = play_refer_data['attribution']
            media_source = attribution.get('mediaSource', '')
            campaign = attribution.get('campaign', '')
            medium = attribution.get('medium', '')

            if media_source:
                parts = []
                if medium:
                    parts.append(f"Medium={medium}")
                if campaign:
                    parts.append(f"Campaign={campaign}")
                if media_source:
                    parts.append(f"Source={media_source}")

                if parts:
                    return f"Clicko ({', '.join(parts)})"
                return f"Clicko ({media_source})"

        install_referrer = play_refer_data.get('installReferrer', '')

        if not install_referrer:
            return "No Tracking"

        # Google Ads (gclid parameter)
        if 'gclid=' in install_referrer:
            gad_source = extract_param(install_referrer, 'gad_source')
            if gad_source:
                mapping = {
                    '1': 'Google Ads - Search',
                    '2': 'Google Ads - Display',
                    '3': 'Google Ads - App Campaign',
                    '5': 'Google Ads - Shopping'
                }
                return mapping.get(gad_source, 'Google Ads - Other')
            return 'Google Ads - Other'

        # Meta Instagram
        if 'utm_campaign=ig4a' in install_referrer or 'apps.instagram.com' in install_referrer or 'instagram' in install_referrer.lower():
            return 'Meta - Instagram'

        # Meta Facebook
        if 'utm_campaign=fb4a' in install_referrer or 'facebook' in install_referrer.lower():
            return 'Meta - Facebook'

        # Telegram
        if 'telegram' in install_referrer.lower() or 'media_source=telegram' in install_referrer:
            return 'Telegram'

        # Website
        if 'prepairo-website' in install_referrer:
            return 'Website'

        # Play Store Organic
        if 'utm_source=google-play' in install_referrer:
            return 'Play Store - Organic'

        # Clicko tracking (click_id parameter)
        if 'click_id=' in install_referrer:
            media_source = extract_param(install_referrer, 'media_source')
            campaign = extract_param(install_referrer, 'campaign')
            medium = extract_param(install_referrer, 'medium')

            parts = []
            if medium:
                parts.append(f"Medium={medium}")
            if campaign:
                parts.append(f"Campaign={campaign}")
            if media_source:
                parts.append(f"Source={media_source}")

            if parts:
                return f"Clicko ({', '.join(parts)})"
            return 'Clicko'

        # Direct / Not Set
        if 'utm_source=(not%20set)' in install_referrer or 'utm_source=(not set)' in install_referrer:
            return 'Direct / Not Set'

        return 'Other'

    except Exception as e:
        logger.warn(f"Failed to parse install channel: {e}")
        return 'Unknown'


def get_install_data(conn, hours: int = 6) -> Dict:
    """Fetch app install data with channel attribution"""

    logger.info(f"Fetching install data for last {hours} hours...")

    # Get total installs (all new users created)
    total_installs_result = execute_query(conn, f"""
        SELECT COUNT(*) as count
        FROM users_profile up
        WHERE up.created_at >= NOW() - INTERVAL '{hours} hours'
            AND up.is_fake_user = false;
    """)
    total_installs = total_installs_result[0]['count'] if total_installs_result else 0

    # Get phone verified users with platform and channel data
    phone_verified = execute_query(conn, f"""
        SELECT
            up.signup_platform,
            up.play_refer,
            up.signup_source,
            up.created_at
        FROM users_profile up
        JOIN users_auth ua ON up.id = ua.id
        WHERE ua.is_phone_no_verified = TRUE
            AND up.created_at >= NOW() - INTERVAL '{hours} hours'
            AND up.is_fake_user = false
        ORDER BY up.created_at DESC;
    """)

    # Parse and categorize phone verified users
    total_phone_verified = len(phone_verified)
    platform_breakdown = {}
    channel_breakdown = {}
    campaign_breakdown = {}

    for user in phone_verified:
        # Platform
        platform = user['signup_platform'] or 'Unknown'
        platform_breakdown[platform] = platform_breakdown.get(platform, 0) + 1

        # Channel (from play_refer for Android, "iOS (No Attribution)" for iOS)
        if platform.lower() == 'ios':
            channel = 'iOS (No Attribution)'
        else:
            channel = parse_install_channel(user['play_refer'])

        channel_breakdown[channel] = channel_breakdown.get(channel, 0) + 1

        # Campaign (extract from play_refer attribution or installReferrer)
        campaign = None
        if user['play_refer']:
            if 'attribution' in user['play_refer']:
                campaign = user['play_refer']['attribution'].get('campaign')
            elif 'installReferrer' in user['play_refer']:
                campaign = extract_param(user['play_refer']['installReferrer'], 'campaign')

        if campaign:
            campaign_breakdown[campaign] = campaign_breakdown.get(campaign, 0) + 1

    return {
        'total_installs': total_installs,
        'total_phone_verified': total_phone_verified,
        'by_platform': platform_breakdown,
        'by_channel': channel_breakdown,
        'by_campaign': campaign_breakdown,
        'raw_data': phone_verified
    }


def get_conversion_data(conn, hours: int = 6) -> Dict:
    """Fetch conversion data with channel attribution"""

    logger.info(f"Fetching conversion data for last {hours} hours...")

    # Get all conversions with platform and channel data
    conversions = execute_query(conn, f"""
        SELECT
            us.user_id,
            us.plan_type,
            us.amount,
            us.subscription_status,
            us.created_at,
            up.signup_platform,
            up.play_refer,
            up.full_name,
            up.phone_number,
            ua.email
        FROM user_subscriptions us
        JOIN users_profile up ON us.user_id = up.id
        JOIN users_auth ua ON us.user_id = ua.id
        WHERE us.created_at >= NOW() - INTERVAL '{hours} hours'
            AND us.subscription_status = 'ACTIVE'
            AND up.is_fake_user = false
        ORDER BY us.created_at DESC;
    """)

    total_conversions = len(conversions)

    if total_conversions == 0:
        return {
            'total': 0,
            'by_platform': {},
            'by_channel': {},
            'by_campaign': {},
            'raw_data': []
        }

    # Parse and categorize
    platform_breakdown = {}
    channel_breakdown = {}
    campaign_breakdown = {}

    for conversion in conversions:
        # Platform
        platform = conversion['signup_platform'] or 'Unknown'
        platform_breakdown[platform] = platform_breakdown.get(platform, 0) + 1

        # Channel
        if platform.lower() == 'ios':
            channel = 'iOS (No Attribution)'
        else:
            channel = parse_install_channel(conversion['play_refer'])

        channel_breakdown[channel] = channel_breakdown.get(channel, 0) + 1

        # Campaign
        campaign = None
        if conversion['play_refer']:
            if 'attribution' in conversion['play_refer']:
                campaign = conversion['play_refer']['attribution'].get('campaign')
            elif 'installReferrer' in conversion['play_refer']:
                campaign = extract_param(conversion['play_refer']['installReferrer'], 'campaign')

        if campaign:
            campaign_breakdown[campaign] = campaign_breakdown.get(campaign, 0) + 1

    return {
        'total': total_conversions,
        'by_platform': platform_breakdown,
        'by_channel': channel_breakdown,
        'by_campaign': campaign_breakdown,
        'raw_data': conversions
    }


def get_purchase_intent_data(conn, hours: int = 6) -> Dict:
    """Fetch all purchase intent data: plus clicks, subscribe clicks, payment clicks, coupon applications"""

    logger.info(f"Fetching purchase intent data for last {hours} hours...")

    # Plus Page Clicks (unique users only - most recent click per user, sorted by time)
    plus_clicks = execute_query(conn, f"""
        SELECT * FROM (
            SELECT DISTINCT ON (pca.user_id)
                up.full_name,
                up.phone_number,
                ua.email,
                pca.created_at,
                CASE WHEN us.id IS NOT NULL THEN true ELSE false END as converted
            FROM plus_click_audit pca
            JOIN users_profile up ON pca.user_id = up.id
            JOIN users_auth ua ON pca.user_id = ua.id
            LEFT JOIN user_subscriptions us ON pca.user_id = us.user_id
                AND us.created_at >= pca.created_at
            WHERE pca.created_at >= NOW() - INTERVAL '{hours} hours'
            ORDER BY pca.user_id, pca.created_at DESC
        ) AS unique_users
        ORDER BY created_at DESC
        LIMIT 50;
    """)

    # Subscribe Now Clicks (unique users only - most recent click per user, sorted by time)
    subscribe_clicks = execute_query(conn, f"""
        SELECT * FROM (
            SELECT DISTINCT ON (sna.user_id)
                up.full_name,
                up.phone_number,
                ua.email,
                sna.subscription_plan,
                sna.created_at,
                CASE WHEN us.id IS NOT NULL THEN true ELSE false END as converted
            FROM subscribe_now_audit sna
            JOIN users_profile up ON sna.user_id = up.id
            JOIN users_auth ua ON sna.user_id = ua.id
            LEFT JOIN user_subscriptions us ON sna.user_id = us.user_id
                AND us.created_at >= sna.created_at
            WHERE sna.created_at >= NOW() - INTERVAL '{hours} hours'
            ORDER BY sna.user_id, sna.created_at DESC
        ) AS unique_users
        ORDER BY created_at DESC
        LIMIT 50;
    """)

    # Payment Method Clicks (unique users only - most recent click per user, sorted by time)
    payment_clicks = execute_query(conn, f"""
        SELECT * FROM (
            SELECT DISTINCT ON (posa.user_id)
                up.full_name,
                up.phone_number,
                ua.email,
                posa.payment_method,
                posa.plan_type,
                posa.created_at,
                CASE WHEN us.id IS NOT NULL THEN true ELSE false END as converted
            FROM payment_option_screen_audit posa
            JOIN users_profile up ON posa.user_id = up.id
            JOIN users_auth ua ON posa.user_id = ua.id
            LEFT JOIN user_subscriptions us ON posa.user_id = us.user_id
                AND us.created_at >= posa.created_at
            WHERE posa.created_at >= NOW() - INTERVAL '{hours} hours'
            ORDER BY posa.user_id, posa.created_at DESC
        ) AS unique_users
        ORDER BY created_at DESC
        LIMIT 50;
    """)

    # Coupon Applications (unique users)
    coupon_result = execute_query(conn, f"""
        SELECT COUNT(DISTINCT user_id) as count
        FROM holiday_coupon_applied_audit
        WHERE created_at >= NOW() - INTERVAL '{hours} hours';
    """)
    coupon_count = coupon_result[0]['count'] if coupon_result else 0

    return {
        'plus_clicks': plus_clicks,
        'subscribe_clicks': subscribe_clicks,
        'payment_clicks': payment_clicks,
        'coupon_count': coupon_count
    }


def format_install_message(data: Dict, hours: int) -> Dict:
    """Format Message 1: App Installs"""

    now_ist = to_ist(datetime.utcnow())

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📱 App Installs - Last {hours} Hours",
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"_{now_ist.strftime('%Y-%m-%d %H:%M IST')}_"
            }]
        },
        {"type": "divider"}
    ]

    # Total installs and phone verified
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*📊 Total Installs: {data['total_installs']}*\n"
                   f"*📞 Phone Verified: {data['total_phone_verified']}*"
        }
    })
    blocks.append({"type": "divider"})

    # Note: Breakdowns are for phone verified users only
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "_Breakdowns below are for phone verified users only_"}]
    })
    blocks.append({"type": "divider"})

    # Platform breakdown
    if data['by_platform']:
        platform_text = "*🔹 By Platform:*\n"
        for platform, count in sorted(data['by_platform'].items(), key=lambda x: x[1], reverse=True):
            platform_text += f"• {platform.upper()}: `{count}`\n"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": platform_text}
        })
        blocks.append({"type": "divider"})

    # Channel breakdown
    if data['by_channel']:
        channel_text = "*🔹 By Channel:*\n"
        for channel, count in sorted(data['by_channel'].items(), key=lambda x: x[1], reverse=True):
            channel_text += f"• {channel}: `{count}`\n"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": channel_text}
        })
        blocks.append({"type": "divider"})

    # Campaign breakdown
    if data['by_campaign']:
        campaign_text = "*🔹 By UTM Campaign:*\n"
        for campaign, count in sorted(data['by_campaign'].items(), key=lambda x: x[1], reverse=True):
            campaign_text += f"• {campaign}: `{count}`\n"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": campaign_text}
        })

    return {"blocks": blocks}


def format_conversion_message(data: Dict, hours: int) -> Dict:
    """Format Message 2: Conversions"""

    now_ist = to_ist(datetime.utcnow())

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"💰 Conversions - Last {hours} Hours",
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"_{now_ist.strftime('%Y-%m-%d %H:%M IST')}_"
            }]
        },
        {"type": "divider"}
    ]

    # Total conversions
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*🎯 Total Conversions: {data['total']}*"
        }
    })

    # Only show breakdowns if there are conversions
    if data['total'] > 0:
        blocks.append({"type": "divider"})

        # Platform breakdown
        if data['by_platform']:
            platform_text = "*🔹 By Platform:*\n"
            for platform, count in sorted(data['by_platform'].items(), key=lambda x: x[1], reverse=True):
                platform_text += f"• {platform.upper()}: `{count}`\n"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": platform_text}
            })
            blocks.append({"type": "divider"})

        # Channel breakdown
        if data['by_channel']:
            channel_text = "*🔹 By Channel:*\n"
            for channel, count in sorted(data['by_channel'].items(), key=lambda x: x[1], reverse=True):
                channel_text += f"• {channel}: `{count}`\n"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": channel_text}
            })
            blocks.append({"type": "divider"})

        # Campaign breakdown
        if data['by_campaign']:
            campaign_text = "*🔹 By UTM Campaign:*\n"
            for campaign, count in sorted(data['by_campaign'].items(), key=lambda x: x[1], reverse=True):
                campaign_text += f"• {campaign}: `{count}`\n"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": campaign_text}
            })

    return {"blocks": blocks}


def format_purchase_intent_summary(data: Dict, hours: int) -> Dict:
    """Format Message 3: User Purchase Intents Summary (metrics only)"""

    now_ist = to_ist(datetime.utcnow())

    plus_clicks = data['plus_clicks']
    subscribe_clicks = data['subscribe_clicks']
    payment_clicks = data['payment_clicks']

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🎯 User Purchase Intents - Last {hours} Hours",
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"_{now_ist.strftime('%Y-%m-%d %H:%M IST')}_"
            }]
        },
        {"type": "divider"}
    ]

    # Summary metrics
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*📊 Summary Metrics*\n"
                   f"• Plus Page Clicks: `{len(plus_clicks)}` unique users\n"
                   f"• Subscribe Now Clicks: `{len(subscribe_clicks)}` unique users\n"
                   f"• Payment Method Clicks: `{len(payment_clicks)}` unique users\n"
                   f"• Coupon Applications: `{data['coupon_count']}` unique users"
        }
    })

    return {"blocks": blocks}


def format_plus_clicks_message(data: Dict, hours: int) -> Dict:
    """Format Message 4: Plus Page Clicks Details"""

    now_ist = to_ist(datetime.utcnow())
    plus_clicks = data['plus_clicks']
    plus_converted = sum(1 for c in plus_clicks if c.get('converted'))

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"➕ Plus Page Clicks - Last {hours} Hours",
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"_{now_ist.strftime('%Y-%m-%d %H:%M IST')}_"
            }]
        },
        {"type": "divider"}
    ]

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Total: {len(plus_clicks)} unique users* (Converted: {plus_converted})"
        }
    })
    blocks.append({"type": "divider"})

    for click in plus_clicks[:20]:
        status = "✅" if click.get('converted') else "⏳"
        click_time_ist = to_ist(click['created_at'])

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{status} *{click['full_name']}*\n"
                       f"  📱 `{click['phone_number']}` | 📧 `{click['email']}`\n"
                       f"  🕐 {click_time_ist.strftime('%b %d, %I:%M %p IST')}"
            }
        })

    if len(plus_clicks) > 20:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"_...and {len(plus_clicks)-20} more_"}]
        })

    return {"blocks": blocks}


def format_subscribe_clicks_message(data: Dict, hours: int) -> Dict:
    """Format Message 5: Subscribe Now Clicks Details"""

    now_ist = to_ist(datetime.utcnow())
    subscribe_clicks = data['subscribe_clicks']
    sub_converted = sum(1 for c in subscribe_clicks if c.get('converted'))

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🔔 Subscribe Now Clicks - Last {hours} Hours",
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"_{now_ist.strftime('%Y-%m-%d %H:%M IST')}_"
            }]
        },
        {"type": "divider"}
    ]

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Total: {len(subscribe_clicks)} unique users* (Converted: {sub_converted})"
        }
    })
    blocks.append({"type": "divider"})

    for click in subscribe_clicks[:20]:
        status = "✅" if click.get('converted') else "⏳"
        click_time_ist = to_ist(click['created_at'])

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{status} *{click['full_name']}*\n"
                       f"  📱 `{click['phone_number']}` | 📧 `{click['email']}`\n"
                       f"  📋 {click['subscription_plan']}\n"
                       f"  🕐 {click_time_ist.strftime('%b %d, %I:%M %p IST')}"
            }
        })

    if len(subscribe_clicks) > 20:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"_...and {len(subscribe_clicks)-20} more_"}]
        })

    return {"blocks": blocks}


def format_payment_clicks_message(data: Dict, hours: int) -> Dict:
    """Format Message 6: Payment Method Clicks Details"""

    now_ist = to_ist(datetime.utcnow())
    payment_clicks = data['payment_clicks']
    pay_converted = sum(1 for c in payment_clicks if c.get('converted'))

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"💳 Payment Method Clicks - Last {hours} Hours",
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"_{now_ist.strftime('%Y-%m-%d %H:%M IST')}_"
            }]
        },
        {"type": "divider"}
    ]

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Total: {len(payment_clicks)} unique users* (Converted: {pay_converted})"
        }
    })
    blocks.append({"type": "divider"})

    for click in payment_clicks[:20]:
        status = "✅" if click.get('converted') else "⏳"
        click_time_ist = to_ist(click['created_at'])

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{status} *{click['full_name']}*\n"
                       f"  📱 `{click['phone_number']}` | 📧 `{click['email']}`\n"
                       f"  💳 {click['payment_method']} | 📋 {click['plan_type']}\n"
                       f"  🕐 {click_time_ist.strftime('%b %d, %I:%M %p IST')}"
            }
        })

    if len(payment_clicks) > 20:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"_...and {len(payment_clicks)-20} more_"}]
        })

    return {"blocks": blocks}


def send_to_slack(message: Dict, message_name: str):
    """Send formatted message to Slack webhook"""
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=message)
        response.raise_for_status()
        logger.info(f"✅ {message_name} sent to Slack successfully")
    except Exception as e:
        logger.error(f"❌ {message_name} failed to send to Slack: {e}")


def main():
    """Main execution function"""
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 6

    try:
        logger.info(f"🚀 Starting analytics report for last {hours} hours...")

        # Connect to database
        conn = get_db_connection()

        # Fetch all data
        install_data = get_install_data(conn, hours)
        conversion_data = get_conversion_data(conn, hours)
        purchase_intent_data = get_purchase_intent_data(conn, hours)

        # Close connection
        conn.close()

        logger.info(f"✅ Data fetched: {install_data['total_installs']} installs, "
                   f"{install_data['total_phone_verified']} phone verified, "
                   f"{conversion_data['total']} conversions")

        # Format and send 6 separate messages
        msg1 = format_install_message(install_data, hours)
        send_to_slack(msg1, "Message 1: Installs")

        msg2 = format_conversion_message(conversion_data, hours)
        send_to_slack(msg2, "Message 2: Conversions")

        msg3 = format_purchase_intent_summary(purchase_intent_data, hours)
        send_to_slack(msg3, "Message 3: Purchase Intents Summary")

        msg4 = format_plus_clicks_message(purchase_intent_data, hours)
        send_to_slack(msg4, "Message 4: Plus Clicks")

        msg5 = format_subscribe_clicks_message(purchase_intent_data, hours)
        send_to_slack(msg5, "Message 5: Subscribe Clicks")

        msg6 = format_payment_clicks_message(purchase_intent_data, hours)
        send_to_slack(msg6, "Message 6: Payment Clicks")

        logger.info("✅ All 6 messages sent successfully")

    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")

        # Send error notification to Slack
        try:
            now_ist = to_ist(datetime.utcnow())
            error_msg = {
                "text": f"❌ *Analytics Report Failed*\n```{str(e)}```\nTime: {now_ist.strftime('%Y-%m-%d %H:%M IST')}"
            }
            requests.post(SLACK_WEBHOOK_URL, json=error_msg)
        except:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
